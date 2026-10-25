"""The Concierge, built with LangGraph by the bank's digital team. It talks to
the customer and hands each part of a request to the specialist that owns it,
all at once, then answers with what they did.

It streams what happens to the demo's page as it happens."""
import contextvars
import json
import os
import queue
import threading

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from opentelemetry import context as otel_context
from opentelemetry import trace
from pydantic import BaseModel

from common import gateway, identity, service, steps

BANK = os.environ.get("BANK_NAME", "the bank")
SPECIALISTS = {
    "cards-agent": os.environ.get("CARDS_AGENT_URL", "http://cards-agent:8000"),
    "travel-desk": os.environ.get("TRAVEL_DESK_URL", "http://travel-desk:8000"),
    "policy-advisor": os.environ.get("POLICY_ADVISOR_URL", "http://policy-advisor:8000"),
}
INSTRUCTIONS = """You are the concierge of %s. You talk to the customer and hand each part of
their request to the specialist that owns it, all at once:
- ask_cards_agent: the customer's debit card: a lost or stolen card, a new one.
- ask_travel_desk: a trip abroad: what paying by card costs there, and travel insurance.
- ask_policy_advisor: options and prices in the bank's catalogue: card delivery, packages, fees, security.
The Cards Agent orders cards but does not know the options: when the customer wants it faster, or
asks about prices, ask the Policy Advisor too.
Give each specialist only its part, in plain words, with the facts it needs (where the
customer is, what happened). Then answer the customer in plain text, without markdown or
lists: four or five short sentences on what was done and what it means for them, with the
useful numbers (references, amounts, delays). Use only what the specialists told you. When a
specialist was stopped from doing something, say simply what was done and what was not. When a
specialist needs something from the customer, ask the customer for it.""" % BANK
SAFE_ANSWER = ("For your security, please never share your full card number, here or anywhere else: I have not "
               "passed it on. No one at %s, and no agent working for us, will ever ask you for it." % BANK)
MAX_TURNS = 6


class ChatAnthropicText(ChatAnthropic):
    """Hands the final answer back as plain text, so the trace shows it as the
    agent's output. Keep "Anthropic" in the name: Agent Manager reads the model
    vendor from it."""

    def _generate(self, *args, **kwargs):
        result = super()._generate(*args, **kwargs)
        message = result.generations[0].message
        if not message.tool_calls:
            message.content = message.text
        return result


model = ChatAnthropicText(model=gateway.MODEL, max_tokens=16000, base_url=gateway.URL, api_key="held-by-agent-manager",
                          default_headers=gateway.HEADERS, **({"effort": gateway.EFFORT} if gateway.EFFORT else {}))
_emit = contextvars.ContextVar("emit")  # where this request's steps go; tools run in threads of their own


def ask(agent, request):
    """Sends one part of the request to a specialist, with a token from the
    Concierge's own Agent Manager identity; the page sees it start and finish."""
    emit = _emit.get()
    emit({"type": "call", "agent": agent, "status": "start", "request": request})
    try:
        bearer = identity.token()
        reply = httpx.post(SPECIALISTS[agent] + "/chat", json={"message": request}, timeout=180,
                           headers={"Authorization": "Bearer " + bearer}).json()
    except identity.Refused as exc:
        reply = {"agent": agent, "refused": str(exc)}
    except (httpx.HTTPError, ValueError) as exc:
        reply = {"agent": agent, "answer": "The %s did not answer." % agent, "steps": [{"kind": "error", "reason": str(exc)}]}
    if reply.get("refused"):
        reply["answer"] = "The %s could not be reached: %s" % (agent, reply["refused"])
    emit({"type": "call", "status": "done", **reply})
    return reply.get("answer", "")


@tool
def ask_cards_agent(request: str) -> str:
    """Ask the Cards Agent to act on the customer's debit card: a lost or stolen card, a new one."""
    return ask("cards-agent", request)


@tool
def ask_travel_desk(request: str) -> str:
    """Ask the Travel Desk about a trip abroad: what paying by card costs there, and travel insurance. Name the country."""
    return ask("travel-desk", request)


@tool
def ask_policy_advisor(question: str) -> str:
    """Ask the Policy Advisor about options and prices in the bank's catalogue: card delivery, packages, fees, security."""
    return ask("policy-advisor", question)


agent = create_agent(model, tools=[ask_cards_agent, ask_travel_desk, ask_policy_advisor],
                     system_prompt=INSTRUCTIONS, name="concierge")
history = {}
app = FastAPI(title="concierge", telemetry={"exclude": lambda scope: scope.get("path") == "/health"})


class Ask(BaseModel):
    message: str
    session_id: str = "demo"


def answer(ask_, emit):
    """Runs one turn of the conversation and emits each step."""
    _emit.set(emit)
    taken = steps.start()
    past = history.setdefault(ask_.session_id, [])
    result = agent.invoke({"messages": past + [{"role": "user", "content": ask_.message}]})
    text = result["messages"][-1].text
    if any(step["kind"] == "blocked" and step["direction"] == "request" for step in taken):
        text = SAFE_ANSWER  # the message never reached the model, and it stays out of the conversation
    else:
        past += [{"role": "user", "content": ask_.message}, {"role": "assistant", "content": text}]
        del past[:-2 * MAX_TURNS]
    return text, taken


@app.post("/chat/stream")
def chat_stream(ask_: Ask):
    events = queue.Queue()
    trace_id = format(trace.get_current_span().get_span_context().trace_id, "032x")
    parent = otel_context.get_current()

    def work():
        token = otel_context.attach(parent)  # the agent's spans belong to this request's trace
        try:
            text, taken = answer(ask_, events.put)
            events.put({"type": "answer", "agent": "concierge", "text": text, "steps": taken, "traceId": trace_id})
        except Exception as exc:  # the page shows what went wrong instead of waiting forever
            events.put({"type": "error", "error": str(exc)[:300]})
        finally:
            otel_context.detach(token)
            events.put(None)

    threading.Thread(target=work, daemon=True).start()

    def stream():
        while (event := events.get()) is not None:
            yield "data: %s\n\n" % json.dumps(event)

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/health")
def health():
    return {"agent": "concierge", "framework": "LangGraph", "version": "v1", "model": gateway.MODEL, "key": gateway.hint()}


service.key_route(app)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
