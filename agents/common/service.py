"""The HTTP service every specialist agent runs, whatever its framework. The
concierge sends it one request, with a token from its Agent Manager identity;
the service checks that identity, then answers with the agent's reply, the
steps it took, and the id of its trace in Agent Manager."""
import logging
import os
import secrets

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from opentelemetry import trace
from pydantic import BaseModel

from common import gateway, identity, steps  # noqa: F401  (gateway watches every model call from here on)

BANK = os.environ.get("BANK_NAME", "the bank")


class Ask(BaseModel):
    message: str


class Release(BaseModel):
    version: str


class Key(BaseModel):
    key: str


def operator(key):
    """Only the demo's operator (the page) may switch an agent's version or setup."""
    if not secrets.compare_digest(key, os.environ.get("RELEASE_KEY", "")):
        raise HTTPException(403, "wrong release key")


def key_route(app):
    """Lets the page hand the agent a new key to the model, as its team would
    after Agent Manager revoked the last one."""
    @app.post("/key")
    def new_key(body: Key, x_release_key: str = Header("")):
        operator(x_release_key)
        gateway.HEADERS[gateway.KEY_HEADER] = body.key
        return {"key": gateway.hint()}


def blocked_reply(reply, taken):
    """When Agent Manager stopped the agent part way, the concierge still learns
    what was done before."""
    done = ["%s: %s" % (step["name"], step["result"]) for step in taken if step["kind"] == "tool" and step["ok"]]
    return reply + ("\nDone before that: " + "; ".join(done) if done else "")


def create(name, framework, answer, versions=None):
    """The service of one agent. answer(message, instructions) returns its reply.
    versions maps each version to its instructions; the first one is live."""
    versions = versions or {"v1": None}
    live = {"version": next(iter(versions))}
    app = FastAPI(title=name, telemetry={"exclude": lambda scope: scope.get("path") != "/chat"})

    @app.post("/chat")
    def chat(ask: Ask, authorization: str = Header("")):
        try:
            caller = identity.check(authorization)
        except identity.Refused as exc:
            return JSONResponse({"agent": name, "refused": str(exc)}, status_code=401)
        taken = steps.start()
        try:
            reply = answer(ask.message, versions[live["version"]])
        except Exception as exc:  # the concierge still gets an answer, and the page shows the failure
            logging.exception("%s failed", name)
            steps.record("error", reason=str(exc)[:200])
            reply = "I could not finish this request."
        if any(step["kind"] == "blocked" for step in taken):
            reply = blocked_reply(reply, taken)
        trace_id = format(trace.get_current_span().get_span_context().trace_id, "032x")
        return {"agent": name, "framework": framework, "version": live["version"], "identity": caller,
                "answer": reply, "steps": taken, "traceId": trace_id}

    @app.get("/health")
    def health():
        return {"agent": name, "framework": framework, "version": live["version"], "model": gateway.MODEL, "key": gateway.hint()}

    key_route(app)

    if len(versions) > 1:
        @app.post("/release")
        def release(body: Release, x_release_key: str = Header("")):
            operator(x_release_key)
            if body.version not in versions:
                raise HTTPException(400, "unknown version")
            live["version"] = body.version
            return health()

    return app
