"""Other agents, reached over A2A through the A2A Gateway of the main demo (the
WSO2 AI Gateway): the bank's Travel Money Agent and its partner's Travel
Insurance Agent, as in its A2A showcases. Each call is recorded as a step."""
import uuid

import httpx

from common import steps


def send(agent, url, text):
    """Sends one message to an agent and returns its answer."""
    message = {"messageId": str(uuid.uuid4()), "role": "ROLE_USER", "parts": [{"text": text}]}
    try:
        # The demo gateway's certificate is its own, not one a public authority signed.
        reply = httpx.post(url, json={"jsonrpc": "2.0", "id": 1, "method": "SendMessage", "params": {"message": message}},
                           headers={"A2A-Version": "1.0"}, timeout=60, verify=False)
        reply.raise_for_status()
        result = reply.json().get("result") or {}
        answer = result.get("message") or ((result.get("task") or {}).get("status") or {}).get("message") or {}
        text, ok = "".join(part.get("text", "") for part in answer.get("parts") or []), True
    except (httpx.HTTPError, ValueError) as exc:
        text, ok = "%s did not answer: %s" % (agent, exc), False
    steps.record("tool", name=agent, via="a2a", ok=ok, result=text)
    return text
