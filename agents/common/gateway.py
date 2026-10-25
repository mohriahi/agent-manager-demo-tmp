"""Every model call an agent makes goes through Agent Manager's gateway, with
the key Agent Manager gave this agent. This module records each call and its
tokens. When one of the agent's guardrails blocks a call, it turns the
gateway's verdict into a short answer the agent's framework understands, so
the agent carries on and the page can show what was blocked and why.

It works for every framework, because they all reach the gateway the same way
underneath."""
import json
import os
import re

import httpx

from common import steps

URL = os.environ["LLM_URL"]
KEY_HEADER = os.environ.get("LLM_KEY_HEADER", "api-key")
KEY = os.environ["LLM_KEY"]
MODEL = os.environ.get("MODEL", "claude-haiku-4-5")
# How hard the model thinks, for the models that take it (Claude 4.6 and later). Empty: not sent.
EFFORT = os.environ.get("EFFORT", "")
HEADERS = {KEY_HEADER: KEY}  # the page hands the agent a new key here after a revocation


def hint():
    """The end of the agent's key, enough to tell which one it holds."""
    return HEADERS[KEY_HEADER][-4:]


def _reason(verdict):
    """A plain-words reason for a block, from the guardrail's own report."""
    report = verdict.get("assessments") or verdict.get("actionReason") or ""
    if verdict.get("direction") == "RESPONSE":
        names = re.findall(r'"([a-z_]+)"', report)
        tool = names[-1] if names else None
        if tool and tool != "name":
            return tool, "the model asked to run %s, which this agent is not allowed to do" % tool
        return None, "the model's answer broke one of this agent's guardrails"
    if r"\d{4}" in report:
        return None, "the message contained a full card number, which must never reach the model"
    return None, "the request broke one of this agent's guardrails"


def _answer(http, request, reason):
    """A short answer in the model's own format, so the agent's framework carries on."""
    try:
        model = json.loads(request.content).get("model", MODEL)
    except ValueError:
        model = MODEL
    answer = {"id": "msg_blocked_by_agent_manager", "type": "message", "role": "assistant", "model": model,
              "content": [{"type": "text", "text": "Agent Manager blocked this step: %s." % reason}],
              "stop_reason": "end_turn", "stop_sequence": None, "usage": {"input_tokens": 0, "output_tokens": 0}}
    return http.Response(200, json=answer, request=request)


def _review(http, request, response):
    """A replacement response for a blocked call, or None to keep the original."""
    if response.status_code == 401:
        reason = "Agent Manager revoked this agent's key to the model"
        steps.record("blocked", direction="key", tool=None, reason=reason)
        return _answer(http, request, reason)
    try:
        body = json.loads(response.content)
    except ValueError:
        return None
    verdict = body.get("message") if isinstance(body.get("message"), dict) else None
    if not verdict or verdict.get("action") != "GUARDRAIL_INTERVENED":
        usage = body.get("usage") or {}
        if response.status_code == 200 and usage:
            steps.record("llm", input=usage.get("input_tokens", 0), output=usage.get("output_tokens", 0))
        return None
    tool, reason = _reason(verdict)
    steps.record("blocked", direction=verdict.get("direction", "").lower(), tool=tool, reason=reason)
    return _answer(http, request, reason)


def _watch(http):
    """Wraps the HTTP library's transports, sync and async."""
    send, send_async = http.HTTPTransport.handle_request, http.AsyncHTTPTransport.handle_async_request

    def handle(self, request):
        if str(request.url).startswith(URL):
            request.headers[KEY_HEADER] = HEADERS[KEY_HEADER]
        response = send(self, request)
        if not str(request.url).startswith(URL):
            return response
        response.read()
        return _review(http, request, response) or response

    async def handle_async(self, request):
        if str(request.url).startswith(URL):
            request.headers[KEY_HEADER] = HEADERS[KEY_HEADER]
        response = await send_async(self, request)
        if not str(request.url).startswith(URL):
            return response
        await response.aread()
        return _review(http, request, response) or response

    http.HTTPTransport.handle_request = handle
    http.AsyncHTTPTransport.handle_async_request = handle_async


# Recent Anthropic SDKs use httpx2, a successor of httpx with the same shape.
_watch(httpx)
try:
    import httpx2
    _watch(httpx2)
except ImportError:
    pass
