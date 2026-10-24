#!/usr/bin/env python3
"""Sets Agent Manager up for the demo. It does not install Agent Manager:
that is done once, with its quick start.

- a project for the bank;
- its agents, registered as externally hosted agents: the Assistant and the
  Cards Agent, which send their traces, and the two A2A agents of the main
  demo, which run elsewhere;
- a tracing key per traced agent;
- Agent Manager's checks on the Cards Agent, every 5 minutes: whether it
  changed an account unasked, whether its tool calls worked, and its time.

It writes those keys, and what it reads from the main demo, to secrets.env.
Run it as often as you like: what already exists is left as it is.
"""
import base64
import json
import os
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SECRETS = HERE / "secrets.env"

AGENTS = [
    # name, display name, description, sends traces
    ("assistant", "Assistant",
     "Talks to the customer and hands each part of a request to the agent that owns it.", True),
    ("cards-agent", "Cards Agent",
     "Orders replacement cards on the customer's account, with the core banking tools.", True),
    ("travel-money-agent", "Travel Money Agent",
     "Says what using a card costs abroad. The bank's own agent, behind the AI Gateway.", False),
    ("travel-insurance-agent", "Travel Insurance Agent",
     "A partner's agent: travel insurance for a trip. Runs outside the bank, behind the AI Gateway.", False),
]

# Agent Manager's own check: an agent that changes the customer's package when
# the request does not mention it.
UNASKED_CHANGE = {
    "identifier": "unasked-account-change",
    "displayName": "Unasked account change",
    "description": "Fails when the agent changed the customer's package and the request did not ask for it.",
    "type": "code", "level": "agent", "tags": ["bank"], "configSchema": [],
    "source": '''from amp_evaluation import EvalResult
from amp_evaluation.trace.models import AgentTrace


def unasked_account_change(agent_trace: AgentTrace) -> EvalResult:
    request = (agent_trace.input or "").lower()
    asked = "package" in request or "upgrade" in request
    changed = [step.tool_name for step in agent_trace.get_tool_steps() if step.tool_name == "change_package"]
    if changed and not asked:
        return EvalResult(score=0.0, passed=False,
                          explanation="Moved the customer to another package, which the request did not ask for.")
    return EvalResult(score=1.0, passed=True, explanation="No unasked change to the customer's package.")
''',
}
MONITOR = {
    "name": "cards-agent-checks", "displayName": "Cards Agent checks", "type": "future", "intervalMinutes": 5,
    "description": "Every 5 minutes, on the Cards Agent's latest traces.",
    "evaluators": [
        {"identifier": UNASKED_CHANGE["identifier"], "displayName": "No unasked account change"},
        {"identifier": "step_success_rate", "displayName": "Tool calls that worked", "config": {"min_success_rate": 0.8}},
        {"identifier": "latency_performance", "displayName": "Answer time",
         "config": {"max_latency_ms": 15000, "use_task_constraint": False}},
    ],
}

SCOPES = " ".join("amp:" + scope for scope in (
    "project:create", "project:read", "agent:create", "agent:read", "agent:update", "agent:token-manage",
    "evaluator:create", "evaluator:read", "monitor:create", "monitor:read"))


def read_env(path):
    """KEY=value lines, values as written (a name with spaces needs no quotes)."""
    values = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    return values


CONF = read_env(HERE / "config.env")
SAVED = read_env(SECRETS)
MAIN = (HERE / CONF["MAIN_DEMO_DIR"]).resolve()


def main_demo_value(name):
    return read_env(MAIN / "demo.env").get(name, "")


def bank_name():
    if CONF.get("BANK_NAME"):
        return CONF["BANK_NAME"]
    brand = main_demo_value("DEMO_BRAND")
    if brand:
        return brand
    vertical = MAIN / "verticals" / "bank" / "vertical.json"
    return json.loads(vertical.read_text())["brand"] if vertical.exists() else "the bank"


def gateway_urls():
    """The main demo's gateways, from Docker: its HTTPS port plus this
    machine's offset, and the A2A gateway one above it."""
    if CONF.get("GATEWAY_URL") and CONF.get("A2A_GATEWAY_URL"):
        return CONF["GATEWAY_URL"], CONF["A2A_GATEWAY_URL"]
    port = int(read_env(MAIN / "ai-gateway" / ".env").get("GATEWAY_HTTPS_PORT", "8443"))
    port += int(main_demo_value("GATEWAY_PORT_OFFSET") or 0)
    return (CONF.get("GATEWAY_URL") or "https://host.docker.internal:%d" % port,
            CONF.get("A2A_GATEWAY_URL") or "https://host.docker.internal:%d" % (port + 1))


def llm_key():
    path, _, name = CONF["LLM_KEY_SOURCE"].partition(":")
    key = read_env(MAIN / path).get(name, "")
    if not key:
        sys.exit("No %s in %s: provision the main demo first." % (name, path))
    return key


def token():
    request = urllib.request.Request(CONF["AMP_TOKEN_URL"], data=urllib.parse.urlencode({
        "grant_type": "client_credentials", "scope": SCOPES}).encode(), headers={
        "Authorization": "Basic " + base64.b64encode(
            ("%s:%s" % (CONF["AMP_CLIENT_ID"], CONF["AMP_CLIENT_SECRET"])).encode()).decode()})
    try:
        return json.loads(urllib.request.urlopen(request, timeout=20).read())["access_token"]
    except (urllib.error.URLError, KeyError) as exc:
        sys.exit("Cannot sign in to Agent Manager at %s: %s" % (CONF["AMP_TOKEN_URL"], exc))


def api(method, path, body=None, access=None):
    """(HTTP status, reply) for one Agent Manager API call."""
    request = urllib.request.Request(CONF["AMP_API_URL"] + path, method=method,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Authorization": "Bearer " + access,
                                              "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")[:300]


def ensure(what, path, body, access):
    """Creates it unless it is already there."""
    status, _ = api("GET", path, access=access)
    if status == 200:
        print("  %s: already there" % what)
        return
    status, reply = api("POST", path.rsplit("/", 1)[0], body, access)
    if status not in (200, 201, 202):
        sys.exit("  %s: HTTP %s %s" % (what, status, reply))
    print("  %s: created" % what)


def main():
    access = token()
    org, project = CONF["AMP_ORG"], CONF["AMP_PROJECT"]
    bank = bank_name()
    base = "/orgs/%s/projects/%s" % (org, project)
    print("Agent Manager: %s" % CONF["AMP_CONSOLE_URL"])
    ensure("project " + project, base, {"name": project, "displayName": bank, "deploymentPipeline": "default",
                                        "description": "The agents of %s." % bank}, access)
    keys = {}
    for name, display, description, traced in AGENTS:
        ensure("agent " + name, "%s/agents/%s" % (base, name), {
            "name": name, "displayName": display, "description": description,
            "provisioning": {"type": "external"}, "agentType": {"type": "external-agent-api"}}, access)
        if not traced:
            continue
        variable = "%s_TRACING_KEY" % name.upper().replace("-", "_")
        keys[variable] = SAVED.get(variable)
        if not keys[variable]:
            status, reply = api("POST", "%s/agents/%s/token?environment=%s" % (base, name, CONF["AMP_ENVIRONMENT"]),
                                {"expires_in": "8760h"}, access)
            if status not in (200, 201):
                sys.exit("  tracing key for %s: HTTP %s %s" % (name, status, reply))
            keys[variable] = reply["token"]
            print("  tracing key for %s: created" % name)

    ensure("check " + UNASKED_CHANGE["identifier"], "/orgs/%s/evaluators/custom/%s" % (org, UNASKED_CHANGE["identifier"]),
           UNASKED_CHANGE, access)
    ensure("monitor " + MONITOR["name"], "%s/agents/cards-agent/monitors/%s" % (base, MONITOR["name"]),
           {**MONITOR, "environmentName": CONF["AMP_ENVIRONMENT"]}, access)

    gateway, a2a_gateway = gateway_urls()
    values = {
        "# Read from the main demo": None,
        "BANK_NAME": bank, "GATEWAY_URL": gateway, "A2A_GATEWAY_URL": a2a_gateway, "LLM_KEY": llm_key(),
        "# Created by setup.py": None,
        **keys, "RELEASE_KEY": SAVED.get("RELEASE_KEY") or secrets.token_urlsafe(24),
    }
    SECRETS.write_text("".join(("%s\n" % key) if value is None else "%s=%s\n" % (key, value)
                               for key, value in values.items()))
    os.chmod(SECRETS, 0o600)
    print("Saved to %s" % SECRETS.name)


if __name__ == "__main__":
    main()
