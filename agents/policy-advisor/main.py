"""The Policy Advisor, built with LlamaIndex by the bank's customer care team.
It answers from the bank's product catalogue, the main demo's own, and only
from it, citing the section behind each answer."""
import asyncio
import os
from pathlib import Path

import uvicorn
from llama_index.core import Document, Settings
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.anthropic import Anthropic
from llama_index.retrievers.bm25 import BM25Retriever
from traceloop.sdk.decorators import tool as traced  # shows each search, and what it found, in Agent Manager

from common import gateway, service, steps


class Claude(Anthropic):
    """The model, without a temperature: the Anthropic SDK under this
    integration no longer takes one."""

    @property
    def _model_kwargs(self):
        kwargs = super()._model_kwargs
        kwargs.pop("temperature", None)
        return kwargs


try:  # Agent Manager's instrumentation: show each model call as a model call, with its tokens
    from opentelemetry.instrumentation.llamaindex.dispatcher_wrapper import AVAILABLE_OPENLLMETRY_INSTRUMENTATIONS
    AVAILABLE_OPENLLMETRY_INSTRUMENTATIONS.append(Claude.__name__)
except ImportError:
    pass

# No embeddings model: the search ranks the documents by their words.
Settings.embed_model = None
model = Claude(model=gateway.MODEL, base_url=gateway.URL, api_key="held-by-agent-manager",
               default_headers=gateway.HEADERS, max_tokens=16000,
               additional_kwargs={"output_config": {"effort": gateway.EFFORT}} if gateway.EFFORT else {})
Settings.llm = model


class TermsRetriever(BM25Retriever):
    """The keyword search, under a name the tracing can read (no digits)."""


def catalogue():
    """The catalogue's sections, one document each, under their titles."""
    text = Path(os.environ.get("CATALOGUE_FILE", "/app/catalogue.md")).read_text().replace("{brand}", service.BANK)
    sections = [part.strip() for part in text.split("\n## ")[1:]]
    return [Document(text=section, metadata={"title": section.splitlines()[0]}) for section in sections]


retriever = TermsRetriever.from_defaults(nodes=catalogue(), similarity_top_k=3)


@traced("search_terms")
def search_terms(query: str) -> str:
    """Search the bank's product catalogue; returns the best matching sections with their titles."""
    found = retriever.retrieve(query)
    steps.record("tool", name="search_terms", ok=True, result=[node.metadata["title"] for node in found])
    return "\n\n".join("[%s] %s" % (node.metadata["title"], node.get_content()) for node in found)


INSTRUCTIONS = """You are the policy advisor of %s. Answer only from the bank's product
catalogue, which you search with search_terms; search for each part of the question. Cite each
section you use by its title in square brackets. Keep it to a few short sentences in plain text,
without markdown, and say so when the catalogue does not cover something.""" % service.BANK


async def advise(message):
    # Without streaming, the run's trace covers the whole answer.
    agent = FunctionAgent(tools=[search_terms], llm=model, streaming=False, system_prompt=INSTRUCTIONS)
    return str(await agent.run(user_msg=message))


def answer(message, _instructions):
    return asyncio.run(advise(message))


app = service.create("policy-advisor", "LlamaIndex", answer)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
