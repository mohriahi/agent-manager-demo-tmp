"""The HTTP service every specialist agent runs, whatever its framework. It
speaks Agent Manager's chat interface, so the console's Try It works too. The
concierge sends it one request, with a token from its Agent Manager identity;
the service checks that identity, then answers with the agent's reply, the
steps it took, and the id of its trace in Agent Manager."""
import logging
import os

from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from opentelemetry import trace
from pydantic import BaseModel

from common import gateway, identity, steps  # noqa: F401  (gateway watches every model call from here on)

BANK = os.environ.get("BANK_NAME", "the bank")


class Ask(BaseModel):
    message: str
    session_id: str = ""


def blocked_reply(reply, taken):
    """When Agent Manager stopped the agent part way, the concierge still learns
    what was done before."""
    done = ["%s: %s" % (step["name"], step["result"]) for step in taken if step["kind"] == "tool" and step["ok"]]
    return reply + ("\nDone before that: " + "; ".join(done) if done else "")


def create(name, framework, answer):
    """The service of one agent. answer(message) returns its reply."""
    app = FastAPI(title=name, telemetry={"exclude": lambda scope: scope.get("path") != "/chat"})

    @app.post("/chat")
    def chat(ask: Ask, authorization: str = Header("")):
        try:
            caller = identity.check(authorization)
        except identity.Refused as exc:
            return JSONResponse({"agent": name, "refused": str(exc)}, status_code=401)
        taken = steps.start()
        try:
            reply = answer(ask.message)
        except Exception as exc:  # the concierge still gets an answer, and the page shows the failure
            logging.exception("%s failed", name)
            steps.record("error", reason=str(exc)[:200])
            reply = "I could not finish this request."
        if any(step["kind"] == "blocked" for step in taken):
            reply = blocked_reply(reply, taken)
        trace_id = format(trace.get_current_span().get_span_context().trace_id, "032x")
        return {"response": reply, "agent": name, "framework": framework, "identity": caller,
                "answer": reply, "steps": taken, "traceId": trace_id}

    @app.get("/health")
    def health():
        return {"agent": name, "framework": framework, "model": gateway.MODEL}

    return app
