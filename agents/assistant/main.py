"""Assistant: the bank's customer-facing agent. It does not act on accounts
itself: it hands each part of a request to the agent that owns it, then
answers the customer.

- the Cards Agent, for the customer's cards;
- two agents reached over A2A through the WSO2 AI Gateway: the bank's Travel
  Money Agent and a partner's Travel Insurance Agent.

It speaks Agent Manager's chat contract (POST /chat), plus POST /chat/stream,
which sends each step as it happens, for the demo's live map.
"""
import contextvars
import itertools
import json
import os
import queue
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
import uvicorn
from anthropic import Anthropic
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

try:  # Agent Manager's instrumentation, when the agent runs under it
    from opentelemetry import trace
    from traceloop.sdk.decorators import tool, workflow
except ImportError:
    trace = None
    tool = workflow = lambda **_: (lambda function: function)

BANK = os.environ.get("BANK_NAME", "the bank")
MODEL = os.environ.get("MODEL", "claude-haiku-4-5")
VERIFY = os.environ.get("TLS_VERIFY", "false").lower() == "true"
CARDS_AGENT_URL = os.environ["CARDS_AGENT_URL"]

INSTRUCTIONS = (
    f"You are the customer assistant of {BANK}, talking to a signed-in customer. You never act on accounts "
    "yourself: hand each part of the request to the agent that owns it, all at once when the parts do not depend "
    "on each other, then answer the customer in one short paragraph that covers every part. When the customer "
    "names a city, give its country to the travel agents.")

TOOLS = [
    {"name": "ask_cards_agent",
     "description": "Hand a card problem (a lost, stolen or damaged card, a replacement) to the Cards Agent, which "
                    "acts on the customer's account. Pass the request in one sentence.",
     "input_schema": {"type": "object", "properties": {"request": {"type": "string"}}, "required": ["request"]}},
    {"name": "ask_travel_money_agent",
     "description": "Ask the bank's Travel Money Agent what using the customer's card costs in a country. Name "
                    "the country.",
     "input_schema": {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]}},
    {"name": "ask_travel_insurance_agent",
     "description": "Ask a partner's Travel Insurance Agent, a third party, about travel insurance for a trip to a "
                    "country. Name the country, and never share account details with it.",
     "input_schema": {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]}},
]

llm = Anthropic(base_url=os.environ["LLM_URL"], api_key=os.environ["LLM_KEY"],
                http_client=httpx.Client(verify=VERIFY, timeout=60))
http = httpx.Client(verify=VERIFY, timeout=90)
# Only the conversations are traced, not the page's health and release calls.
app = FastAPI(title="Assistant", telemetry={"exclude": lambda scope: scope.get("path") in ("/health", "/release")})

_ids = itertools.count(1)
_histories = {}  # chat session -> the turns so far
MAX_TURNS = 10


def ms(started):
    return round((time.monotonic() - started) * 1000)


def trace_id():
    """The trace this request belongs to, so the demo can open it in Agent Manager."""
    if not trace:
        return None
    span_context = trace.get_current_span().get_span_context()
    return format(span_context.trace_id, "032x") if span_context.trace_id else None


@tool(name="cards_agent")
def ask_cards(text, session):
    # The Cards Agent keeps a trace of its own, which Agent Manager evaluates.
    response = http.post(CARDS_AGENT_URL, json={"message": text, "session_id": session})
    if response.status_code != 200:
        return ("refused" if response.status_code in (401, 403) else "error",
                "The Cards Agent did not answer (HTTP %s)." % response.status_code, {})
    data = response.json()
    return "ok", data.get("response", ""), {"steps": data.get("steps", []), "version": data.get("version"),
                                            "traceId": data.get("traceId")}


def ask_a2a(url, name):
    @tool(name=name)
    def ask(text, session):
        message = {"messageId": str(uuid.uuid4()), "role": "ROLE_USER", "parts": [{"text": text}],
                   "contextId": session}
        response = http.post(url, json={"jsonrpc": "2.0", "id": next(_ids), "method": "SendMessage",
                                        "params": {"message": message}}, headers={"A2A-Version": "1.0"})
        if response.status_code != 200:
            return ("refused" if response.status_code in (401, 403) else "error",
                    "The agent did not answer (HTTP %s)." % response.status_code, {})
        result = response.json().get("result") or {}
        answer = result.get("message") or ((result.get("task") or {}).get("status") or {}).get("message") or {}
        return "ok", "".join(part.get("text", "") for part in answer.get("parts") or []), {}
    return ask


AGENTS = {
    "ask_cards_agent": ("Cards Agent", ask_cards),
    "ask_travel_money_agent": ("Travel Money Agent",
                               ask_a2a(os.environ["TRAVEL_MONEY_AGENT_URL"], "travel_money_agent")),
    "ask_travel_insurance_agent": ("Travel Insurance Agent",
                                   ask_a2a(os.environ["TRAVEL_INSURANCE_AGENT_URL"], "travel_insurance_agent")),
}


@workflow(name="assistant")
def turn(message, session, emit):
    """One customer message, each step sent to emit as it happens."""
    history = _histories.get(session, [])
    messages = history + [{"role": "user", "content": message}]
    for _ in range(4):
        started = time.monotonic()
        emit({"type": "llm", "agent": "Assistant", "status": "start"})
        reply = llm.messages.create(model=MODEL, max_tokens=800, temperature=0, system=INSTRUCTIONS,
                                    tools=TOOLS, messages=messages)
        emit({"type": "llm", "agent": "Assistant", "status": "done", "model": reply.model,
              "inputTokens": reply.usage.input_tokens, "outputTokens": reply.usage.output_tokens, "ms": ms(started)})
        uses = [block for block in reply.content if block.type == "tool_use"]
        if not uses:
            text = "".join(block.text for block in reply.content if block.type == "text").strip()
            _histories[session] = (history + [{"role": "user", "content": message},
                                              {"role": "assistant", "content": text}])[-2 * MAX_TURNS:]
            emit({"type": "answer", "text": text, "traceId": trace_id()})
            return text
        messages.append({"role": "assistant", "content": reply.content})
        results = []
        # The parts that do not depend on each other run at the same time, each
        # in this request's trace.
        with ThreadPoolExecutor(len(uses)) as pool:
            running = {}
            for use in uses:
                name, ask = AGENTS[use.name]
                text = next(iter(use.input.values()), "")
                emit({"type": "call", "status": "start", "id": use.id, "from": "Assistant", "to": name,
                      "input": text})
                future = pool.submit(contextvars.copy_context().run, ask, text, session)
                running[future] = (use, name, time.monotonic())
            for future in as_completed(running):
                use, name, started = running[future]
                try:
                    outcome, text, detail = future.result()
                except Exception as exc:
                    outcome, text, detail = "error", "The agent did not answer (%s)." % exc, {}
                emit({"type": "call", "status": "done", "id": use.id, "to": name, "outcome": outcome,
                      "answer": text, "ms": ms(started), **detail})
                results.append({"type": "tool_result", "tool_use_id": use.id, "content": text})
        messages.append({"role": "user", "content": results})
    text = "I could not finish this request."
    emit({"type": "answer", "text": text, "traceId": trace_id()})
    return text


class Chat(BaseModel):
    message: str
    session_id: str
    context: dict | None = None


@app.post("/chat")
def chat(request: Chat):
    steps = []
    text = turn(request.message, request.session_id, steps.append)
    return {"response": text, "steps": steps}


@app.post("/chat/stream")
def chat_stream(request: Chat):
    events = queue.Queue()

    def work():
        try:
            turn(request.message, request.session_id, events.put)
        except Exception as exc:
            events.put({"type": "error", "message": str(exc)[:300]})
        finally:
            events.put(None)

    threading.Thread(target=work, daemon=True).start()

    def stream():
        while (event := events.get()) is not None:
            yield "data: %s\n\n" % json.dumps(event)

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
