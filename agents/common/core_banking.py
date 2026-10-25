"""The bank's Core Banking system, reached through the MCP Gateway of the main
demo (the WSO2 AI Gateway): the same server and the same customer as in its
MCP showcases. Each request an agent handles opens its own MCP session, as a
chat does in the main demo. Each tool call is recorded as a step."""
import contextvars
import json
import os

import httpx

from common import steps

URL = os.environ["MCP_URL"]
_session = contextvars.ContextVar("mcp_session", default=None)


def _post(body, session=None):
    headers = {"Accept": "application/json, text/event-stream", **({"mcp-session-id": session} if session else {})}
    # The demo gateway's certificate is its own, not one a public authority signed.
    return httpx.post(URL, json=body, headers=headers, timeout=30, verify=False)


def open_session():
    """Starts the MCP session of the request in progress. Call it before the agent runs."""
    reply = _post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "bank-agent", "version": "1.0"}}})
    session = reply.headers.get("mcp-session-id")
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"}, session)
    _session.set(session)


def call(tool, **arguments):
    """Runs one Core Banking tool and returns its result."""
    try:
        reply = _post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                       "params": {"name": tool, "arguments": arguments}}, _session.get())
        reply.raise_for_status()
        result = reply.json()["result"]
        text = "".join(block.get("text", "") for block in result.get("content", []))
        ok = not result.get("isError")
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        text, ok = "The MCP Gateway did not answer: %s" % exc, False
    try:
        result = json.loads(text)
    except ValueError:
        result = text
    steps.record("tool", name=tool, via="mcp", ok=ok, result=result)
    return result
