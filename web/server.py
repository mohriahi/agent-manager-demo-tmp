#!/usr/bin/env python3
"""The demo's page: the customer's chat, the bank's agents, and for every act
the screen of Agent Manager that shows it. It relays the Concierge's steps as
they happen, and makes the bank's moves through Agent Manager's API, as its
teams would in the console: try a new version, check it against the bank's
bar, suspend an agent, add a rule, investigate, report.

It also plays the partner's network in the incident: the Travel Desk reaches
the partner's agent through it, and gets either the card the gateway vetted
or the partner's own.

Python standard library only, so the stock Python image runs it as is. The
fleet comes from configure/fleet.py, the same file that sets Agent Manager up."""
import base64
import json
import os
import re
import ssl
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, "/configure")
import fleet  # noqa: E402

ENV = os.environ
CONSOLE = ENV["AMP_CONSOLE_URL"].rstrip("/")
ORG, PROJECT = ENV["AMP_ORG"], ENV["AMP_PROJECT"]
ENVIRONMENT, TRIAL = ENV["AMP_ENVIRONMENT"], ENV["AMP_TRIAL_ENVIRONMENT"]
PROJECT_PAGE = "%s/org/%s/project/%s" % (CONSOLE, ORG, PROJECT)
API_PROJECT = "/orgs/%s/projects/%s" % (ORG, PROJECT)
STATIC = {"/": "index.html", "/app.js": "app.js", "/styles.css": "styles.css"}
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css"}
SCOPES = ("amp:project:read amp:agent:read amp:agent:update amp:agent:suspend amp:agent:env-production "
          "amp:agent:env-non-production amp:environment:read amp:org:view amp:llm-provider:read "
          "amp:llm-provider:connect amp:llm-provider:configure-guardrail amp:monitor:create amp:monitor:read "
          "amp:monitor:score-read amp:observability:trace-read")
HOSTED = [agent["name"] for agent in fleet.AGENTS if agent["runs"] == "platform"]
TRAVEL_DESK = fleet.LIVE_RULE["agent"]
PLANS = {"readiness": (fleet.READINESS, TRIAL), "incident": (fleet.INVESTIGATION, ENVIRONMENT)}


def agent_page(agent, *parts):
    return "/".join(("%s/agents/%s" % (PROJECT_PAGE, agent),) + parts)


def env_page(agent, environment, *parts):
    return agent_page(agent, "environment", environment, *parts)


def trace_page(agent, trace_id, environment=ENVIRONMENT):
    return env_page(agent, environment, "observability", "traces?timeRange=1d&selectedTrace=%s" % trace_id)


_token = {"value": None, "until": 0}


def access():
    """A token for Agent Manager's API, from the quick start's admin client."""
    if time.time() > _token["until"]:
        request = urllib.request.Request(ENV["AMP_TOKEN_URL"], data=urllib.parse.urlencode({
            "grant_type": "client_credentials", "scope": SCOPES}).encode(), headers={
            "Authorization": "Basic " + base64.b64encode(
                ("%s:%s" % (ENV["AMP_CLIENT_ID"], ENV["AMP_CLIENT_SECRET"])).encode()).decode()})
        reply = json.loads(urllib.request.urlopen(request, timeout=10).read())
        _token.update(value=reply["access_token"], until=time.time() + reply.get("expires_in", 600) - 60)
    return _token["value"]


def amp(path, method="GET", body=None):
    """One call to the Agent Manager API."""
    request = urllib.request.Request(ENV["AMP_API_URL"] + path, method=method,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Authorization": "Bearer " + access(), "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(request, timeout=30).read() or b"{}")


def call(url, body=None, headers=None, timeout=10):
    """(HTTP status, JSON reply) of one call to an agent."""
    request = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(text)
        except ValueError:
            return exc.code, {"error": text[:200]}
    except (urllib.error.URLError, OSError) as exc:
        return 0, {"error": str(exc)}


# Where each build runs, and the Suspend button.

def releases():
    """For each agent Agent Manager runs: in each environment, its state and
    the commit of the build that runs there."""
    found = {}
    for agent in HOSTED:
        found[agent] = {}
        for environment, deployment in amp("%s/agents/%s/deployments" % (API_PROJECT, agent)).items():
            image = deployment.get("imageId") or ""
            found[agent][environment] = {"status": deployment.get("status"), "name": deployment.get("environmentDisplayName"),
                                         "commit": image.rsplit("-", 1)[-1][:7] if image else None}
    return found


def state(agent, environment=ENVIRONMENT):
    return amp("%s/agents/%s/deployments" % (API_PROJECT, agent)).get(environment, {}).get("status")


def suspend(on):
    """Suspends the Travel Desk in production, as the console's Suspend button
    does, or deploys it again. Waits until it is done; returns how long it took."""
    started = time.time()
    amp("%s/agents/%s/deployments/state" % (API_PROJECT, TRAVEL_DESK), "POST",
        {"environment": ENVIRONMENT, "state": "Undeploy" if on else "Active"})
    time.sleep(2)
    target = "suspended" if on else "active"
    while time.time() - started < 300 and state(TRAVEL_DESK) != target:
        time.sleep(2)
    return round(time.time() - started)


# The rule the risk team adds in act 4, on the Travel Desk's model calls.

def model_config(agent):
    """The path of an agent's access to the model, and how Agent Manager has it now."""
    base = "%s/agents/%s/model-configs" % (API_PROJECT, agent)
    config = next(item for item in amp(base)["configs"] if item["name"] == "claude")
    path = "%s/%s" % (base, config["uuid"])
    return path, amp(path)


def rule_on(current=None):
    current = current or model_config(TRAVEL_DESK)[1]
    policies = current["envMappings"][ENVIRONMENT]["configuration"].get("policies", [])
    return fleet.THIRD_PARTY_INSTRUCTIONS["regex"] in json.dumps(policies)


def apply(on):
    """Puts the live rule on the Travel Desk in production, or takes it off,
    then waits until its gateway applies it. Returns how long that took."""
    started = time.time()
    path, current = model_config(TRAVEL_DESK)
    rules = fleet.LIVE_RULE["rules"] if on else next(item for item in fleet.AGENTS if item["name"] == TRAVEL_DESK)["rules"]
    environments = list(current["envMappings"])
    body = fleet.model_access(rules, [ENVIRONMENT], variables=True)
    for environment in environments:  # the other environments keep their rules
        if environment != ENVIRONMENT:
            body["envMappings"][environment] = {"providerName": fleet.PROVIDER["id"], "configuration": {
                "policies": current["envMappings"][environment]["configuration"].get("policies", [])}}
    amp(path, "PUT", body)
    while time.time() - started < 60:
        time.sleep(2)
        now = model_config(TRAVEL_DESK)[1]
        if rule_on(now) == on and now["envMappings"][ENVIRONMENT]["configuration"].get("status", "active") == "active":
            break
    time.sleep(3)  # the gateway takes the new rules a moment after Agent Manager reports them
    return round(time.time() - started)


# What Agent Manager recorded and found: traces, checks, scores.

def traces(agent, minutes, limit=50, environment=ENVIRONMENT):
    """An agent's traces of the last minutes, newest first, from Agent Manager."""
    now = time.time()
    query = urllib.parse.urlencode({
        "organization": ORG, "project": PROJECT, "agent": agent, "environment": environment, "limit": str(limit),
        "sortOrder": "desc", "startTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - minutes * 60)),
        "endTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now + 60))})
    return amp_traces("/traces?" + query).get("traces", []), query


def amp_traces(path):
    """One read from Agent Manager's traces API."""
    request = urllib.request.Request(ENV["AMP_TRACES_URL"] + path, headers={"Authorization": "Bearer " + access()})
    return json.loads(urllib.request.urlopen(request, timeout=30).read())


def unwrap(text):
    """A span's output as plain text: it is stored as JSON, sometimes twice."""
    for _ in range(3):
        try:
            value = json.loads(text)
        except (ValueError, TypeError):
            break
        text = value if isinstance(value, str) else json.dumps(value)
    return text


HIDDEN = re.compile(r"note to the (calling )?agent|ask (them|the customer) for|full card number|expiry date", re.I)


def pinpoint(agent, trace_id):
    """Where, in one of an agent's traces, a third party slipped it an
    instruction: the step, and what it said. Read from Agent Manager's trace."""
    _, query = traces(agent, 60, limit=1)
    spans = amp_traces("/traces/%s/spans?%s" % (trace_id, query.replace("limit=1", "limit=200"))).get("spans", [])
    for span in spans:
        if not span["spanName"].endswith(".tool"):
            continue
        detail = amp_traces("/traces/%s/spans/%s?%s" % (trace_id, span["spanId"], query)).get("ampAttributes", {})
        output = unwrap(detail.get("output") or "")
        found = HIDDEN.search(output)
        if found:
            # The whole sentence that carries the instruction.
            start = max(output.rfind(". ", 0, found.start()) + 2, output.rfind('"', 0, found.start()) + 1)
            ends = [i for i in (output.find(". ", found.end()), output.find('."', found.end())) if i != -1]
            excerpt = output[start:min(ends) + 1 if ends else len(output)]
            return {"step": span["spanName"].removesuffix(".tool"), "excerpt": excerpt, "traceUrl": trace_page(agent, trace_id)}
    return None


def evaluate(kind):
    """Asks Agent Manager to run some of the bank's checks on the last minutes
    of an agent's traffic: v2's readiness in the test environment, or the
    incident in production. A one-off run, kept in the console."""
    plan, environment = PLANS[kind]
    now = time.time()
    name = "%s-%s" % (kind, time.strftime("%d%H%M%S", time.gmtime(now)))
    titles = {"incident": "Incident %s investigation", "readiness": "Readiness check %s"}
    body = {
        "name": name, "displayName": titles[kind] % time.strftime("%H:%M", time.gmtime(now)),
        "description": "The bank's checks, on the last %d minutes." % plan["minutes"], "environmentName": environment,
        "type": "past", "evaluators": plan["evaluators"], "llmProvider": {"providerName": fleet.JUDGE_PROVIDER["id"]},
        "traceStart": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - plan["minutes"] * 60)),
        "traceEnd": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))}
    for attempt in (1, 2):  # Agent Manager now and then fails a first try
        try:
            amp("%s/agents/%s/monitors" % (API_PROJECT, plan["agent"]), "POST", body)
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 409:
                break
            if attempt == 2 or exc.code < 500:
                raise
            time.sleep(3)
    return {"kind": kind, "name": name, "url": env_page(plan["agent"], environment, "evaluation", "monitor", "view", name)}


def findings(kind, name):
    """Where a run of checks stands, and for each check: how many traces it
    failed, of how many, with its explanation and the latest failing trace."""
    plan, environment = PLANS[kind]
    agent = plan["agent"]
    runs = amp("%s/agents/%s/monitors/%s/runs" % (API_PROJECT, agent, name)).get("runs", [])
    status = runs[0]["status"] if runs else "pending"
    found = {}
    if status == "success":
        for item in traces(agent, plan["minutes"] + 10, environment=environment)[0]:
            scores = amp("%s/agents/%s/traces/%s/scores" % (API_PROJECT, agent, item["traceId"])).get("monitors", [])
            for monitor in scores:
                if monitor.get("monitorName") != name:
                    continue
                # Trace-level checks score the trace, agent-level ones its agent's span.
                for evaluator in monitor.get("evaluators", []) + [item for span in monitor.get("spans", [])
                                                                   for item in span.get("evaluators", [])]:
                    if evaluator.get("score") is None:
                        continue
                    entry = found.setdefault(evaluator["evaluatorName"], {
                        "check": evaluator["evaluatorName"], "traces": 0, "failed": 0, "explanation": "", "traceUrl": None})
                    entry["traces"] += 1
                    if evaluator["score"] < 0.5:
                        entry["failed"] += 1
                        if not entry["traceUrl"]:  # traces come newest first
                            entry.update(explanation=evaluator.get("explanation", ""),
                                         traceUrl=trace_page(agent, item["traceId"], environment))
    return {"kind": kind, "status": status, "checks": list(found.values())}


def report():
    """Monday's report for the risk committee, from Agent Manager: what each
    agent did over the last day, what it cost, what was blocked, how it scores."""
    rows = []
    for agent in fleet.AGENTS:
        listed, _ = traces(agent["name"], 24 * 60, limit=200)
        usage = [item.get("tokenUsage") or {} for item in listed]
        blocked = sum(1 for item in listed if "Agent Manager blocked" in (item.get("output") or ""))
        rows.append({"agent": agent["name"], "displayName": agent["displayName"], "framework": agent["framework"],
                     "runs": agent["runs"], "requests": len(listed), "tokens": sum(item.get("totalTokens", 0) for item in usage),
                     "input": sum(item.get("inputTokens", 0) for item in usage),
                     "output": sum(item.get("outputTokens", 0) for item in usage), "blocked": blocked,
                     "errors": sum((item.get("status") or {}).get("errorCount", 0) for item in listed)})
    return {"agents": rows, "scores": checks(), "releases": releases()}


def scores(agent):
    """Agent Manager's latest scores of one agent: for each check, its last run
    that scored something (a run with no traffic, or a judge that could not
    answer, leaves no score)."""
    base = "%s/agents/%s/monitors/%s-checks" % (API_PROJECT, agent, agent)
    runs = [run for run in amp(base + "/runs").get("runs", []) if run.get("status") == "success"][:6]
    found, last_run = {}, None
    for run in runs:
        for item in amp("%s/runs/%s/scores" % (base, run["id"])).get("evaluators", []):
            name, mean = item["evaluatorName"], item.get("aggregations", {}).get("mean")
            if name not in found or (found[name]["score"] is None and mean is not None):
                found[name] = {"name": name, "score": mean, "traces": item.get("count", 0) - item.get("skippedCount", 0)}
                if mean is not None and last_run is None:
                    last_run = run.get("completedAt")
        if found and all(item["score"] is not None for item in found.values()):
            break
    return {"agent": agent, "lastRun": last_run, "evaluators": list(found.values())}


_checks = {"at": 0, "value": None}
_checks_lock = threading.Lock()


def checks():
    with _checks_lock:
        if time.time() - _checks["at"] > 20:
            _checks.update(at=time.time(), value=[scores(agent["name"]) for agent in fleet.AGENTS])
        return _checks["value"]


_links = {}


def links():
    """Where each part of the demo lives in the console. Read again every
    minute: the ids behind some screens change when ./run.sh sets them up again."""
    if time.time() - _links.get("at", 0) > 60:
        provider = amp("/orgs/%s/llm-providers/%s" % (ORG, fleet.PROVIDER["id"]))
        agents = {}
        for agent in fleet.AGENTS:
            name = agent["name"]
            configs = amp("%s/agents/%s/model-configs" % (API_PROJECT, name))["configs"]
            rules = agent_page(name, "configure")
            if configs:
                rules = agent_page(name, "configure", "llm-providers", "view", configs[0]["uuid"])
            agents[name] = {"overview": agent_page(name), "rules": rules, "agentId": agent_page(name, "agent-id"),
                            "deploy": agent_page(name, "deployment"), "builds": agent_page(name, "build"),
                            "security": env_page(name, ENVIRONMENT, "security"),
                            "tryTrial": env_page(name, TRIAL, "tryOut", "chat"),
                            "logs": env_page(name, ENVIRONMENT, "observability", "logs"),
                            "traces": env_page(name, ENVIRONMENT, "observability", "traces?timeRange=1d"),
                            "checks": env_page(name, ENVIRONMENT, "evaluation", "monitor", "view", "%s-checks" % name)}
        _links.update(at=time.time(), fleet=PROJECT_PAGE, agents=agents,
                      pipelines="%s/org/%s/deployment-pipelines" % (CONSOLE, ORG),
                      environments="%s/org/%s/environments" % (CONSOLE, ORG),
                      model="%s/org/%s/llm-providers/view/%s" % (CONSOLE, ORG, provider["uuid"]))
    return {key: value for key, value in _links.items() if key != "at"}


def account():
    """The customer's account as it starts in every new chat, read through the
    main demo's MCP Gateway (each chat has its own MCP session)."""
    context = ssl._create_unverified_context()  # the demo gateway's own certificate
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}

    def post(body, session=None):
        request = urllib.request.Request(ENV["MCP_URL"], data=json.dumps(body).encode(),
                                         headers={**headers, **({"mcp-session-id": session} if session else {})})
        return urllib.request.urlopen(request, context=context, timeout=15)

    with post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "demo-page", "version": "1.0"}}}) as reply:
        session = reply.headers.get("mcp-session-id")
    post({"jsonrpc": "2.0", "method": "notifications/initialized"}, session).close()
    with post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
               "params": {"name": "get_account_details", "arguments": {}}}, session) as reply:
        result = json.loads(reply.read())["result"]
    return json.loads("".join(block.get("text", "") for block in result["content"]))


def try_v2(message):
    """Sends a message to the new version of the Cards Agent in the test
    environment, as a tester would with the console's Try It."""
    if not ENV.get("CARDS_AGENT_TRIAL_URL"):
        raise RuntimeError("No v2 in the test environment yet: run ./run.sh once v2 is on GitHub.")
    status, reply = call(ENV["CARDS_AGENT_TRIAL_URL"] + "/chat", {"message": message, "session_id": "trial"},
                         {"X-API-Key": ENV["CARDS_AGENT_TRIAL_KEY"]}, timeout=180)
    if status != 200:
        raise RuntimeError("The new version did not answer (HTTP %s)." % status)
    changed = [step for step in reply.get("steps", []) if step.get("name") == "change_package" and step.get("ok")]
    result = changed[0].get("result") if changed else None
    return {"answer": reply.get("answer"), "steps": reply.get("steps", []), "packageChanged": bool(changed),
            "package": result.get("newPackage") if isinstance(result, dict) else None,
            "traceUrl": trace_page(fleet.READINESS["agent"], reply.get("traceId"), TRIAL)}


def agent_token(agent):
    """A token from an agent's own identity, as that agent would get one."""
    request = urllib.request.Request(ENV["AMP_AGENTID_TOKEN_ENDPOINT"], data=b"grant_type=client_credentials", headers={
        "Authorization": "Basic " + base64.b64encode(("%s:%s" % (
            ENV["%s_CLIENT_ID" % agent], ENV["%s_CLIENT_SECRET" % agent])).encode()).decode()})
    return json.loads(urllib.request.urlopen(request, timeout=10).read())["access_token"]


def callers():
    """Who may command the Cards Agent in production, beside the Concierge: a
    script with no identity, and the Policy Advisor, a registered agent with
    an identity of its own. Agent Manager's gateway answers both."""
    url = ENV["CARDS_AGENT_URL"] + "/chat"
    body = {"message": "Move the customer to the Private package.", "session_id": "rogue"}
    tried = [("A script with no identity", {}),
             ("The Policy Advisor, with its own identity", {"Authorization": "Bearer " + agent_token("POLICY_ADVISOR")})]
    return [{"who": who, "status": call(url, body, headers)[0]} for who, headers in tried]


# The partner's network, in the incident: the partner's vetted card or its own.

partner = {"card": "vetted"}


def relay(handler, method):
    """Passes a call of the Travel Desk on to the partner's agent, through the
    A2A Gateway, and its answer back."""
    route = ENV["TRAVEL_INSURANCE_OWN_URL" if partner["card"] == "own" else "TRAVEL_INSURANCE_URL"]
    length = int(handler.headers.get("Content-Length") or 0)
    request = urllib.request.Request(route + handler.path[len("/partner-agent"):], method=method,
                                     data=handler.rfile.read(length) if length else None,
                                     headers={key: value for key, value in handler.headers.items()
                                              if key.lower() in ("content-type", "accept", "a2a-version")})
    try:
        response = urllib.request.urlopen(request, context=ssl._create_unverified_context(), timeout=60)
        status, body, kind = response.status, response.read(), response.headers.get("Content-Type", "application/json")
    except urllib.error.HTTPError as exc:
        status, body, kind = exc.code, exc.read(), "application/json"
    except (urllib.error.URLError, OSError) as exc:
        status, body, kind = 502, json.dumps({"error": str(exc)}).encode(), "application/json"
    handler.send_response(status)
    handler.send_header("Content-Type", kind)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def control():
    """What applies right now: the partner's card, the live rule, and where each build runs."""
    return {"partner": partner["card"], "rule": rule_on(), "releases": releases()}


def reset():
    """The demo starts over: the partner's vetted card, no live rule, the Travel Desk running."""
    partner["card"] = "vetted"
    if rule_on():
        apply(False)
    if state(TRAVEL_DESK) != "active":
        suspend(False)
    return control()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if not self.path.startswith(("/api/config", "/api/checks", "/api/control", "/api/evaluation")):
            super().log_message(fmt, *args)

    def _json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return {}

    def do_GET(self):
        if self.path.startswith("/partner-agent"):
            return relay(self, "GET")
        path = self.path.split("?")[0]
        query = dict(urllib.parse.parse_qsl(self.path.partition("?")[2]))
        if path == "/api/config":
            try:
                console = links()
            except (urllib.error.URLError, OSError, KeyError, ValueError) as exc:
                console = {"error": "Agent Manager did not answer: %s" % exc}
            return self._json(200, {
                "bank": ENV.get("BANK_NAME", "the bank"), "customer": ENV.get("CUSTOMER_NAME", ""), "model": ENV.get("MODEL"),
                "mainDemoUrl": ENV.get("MAIN_DEMO_URL", "").rstrip("/"), "console": console,
                "environment": ENVIRONMENT, "trial": TRIAL, "trialReady": bool(ENV.get("CARDS_AGENT_TRIAL_URL")),
                "agents": [{key: agent[key] for key in ("name", "displayName", "framework", "description", "runs")}
                           for agent in fleet.AGENTS]})
        if path == "/api/account":
            try:
                return self._json(200, account())
            except (urllib.error.URLError, OSError, KeyError, ValueError) as exc:
                return self._json(502, {"error": "The MCP Gateway did not answer: %s" % exc})
        work = {"/api/control": control, "/api/report": report, "/api/checks": checks,
                "/api/pinpoint": lambda: pinpoint(query.get("agent", TRAVEL_DESK), query.get("trace", "")),
                "/api/evaluation": lambda: findings(query.get("kind", "incident"), query.get("name", ""))}
        if path in work:
            return self._agent_manager(work[path])
        if path in STATIC:
            file = HERE / STATIC[path]
            body = file.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", TYPES[file.suffix])
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return self.wfile.write(body)
        self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path.startswith("/partner-agent"):
            return relay(self, "POST")
        if self.path == "/api/chat":
            return self._chat(self._body())
        body = self._body()
        work = {
            "/api/callers": callers,
            "/api/try-v2": lambda: try_v2(str(body.get("message", ""))[:2000]),
            "/api/evaluate": lambda: evaluate("readiness" if body.get("kind") == "readiness" else "incident"),
            "/api/partner": lambda: partner.update(card="own" if body.get("card") == "own" else "vetted") or partner,
            "/api/suspend": lambda: {"suspended": bool(body.get("on")), "seconds": suspend(bool(body.get("on")))},
            "/api/rule": lambda: {"on": bool(body.get("on")), "seconds": apply(bool(body.get("on")))},
            "/api/reset": reset,
        }
        if self.path in work:
            return self._agent_manager(work[self.path])
        self._json(404, {"error": "not found"})

    def _agent_manager(self, work):
        """Runs some work against Agent Manager, and answers with its result."""
        try:
            return self._json(200, work())
        except (urllib.error.URLError, OSError, KeyError, ValueError, IndexError, StopIteration) as exc:
            return self._json(502, {"error": "Agent Manager did not answer: %s" % exc})
        except RuntimeError as exc:
            return self._json(502, {"error": str(exc)})

    def _chat(self, body):
        """Relays the Concierge's steps as they happen, each with the link to
        its trace in Agent Manager."""
        request = urllib.request.Request(ENV["CONCIERGE_URL"] + "/chat/stream", data=json.dumps({
            "message": str(body.get("message", ""))[:2000], "session_id": str(body.get("session", "demo"))[:100],
        }).encode(), headers={"Content-Type": "application/json"})
        try:
            upstream = urllib.request.urlopen(request, timeout=300)
        except (urllib.error.URLError, OSError) as exc:
            return self._json(502, {"error": "The Concierge does not answer: %s" % exc})
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        with upstream:
            for line in upstream:
                if not line.startswith(b"data:"):
                    continue
                event = json.loads(line[5:])
                if event.get("traceId") and event.get("agent"):
                    event["traceUrl"] = trace_page(event["agent"], event["traceId"])
                self.wfile.write(b"data: %s\n\n" % json.dumps(event).encode())
                self.wfile.flush()


if __name__ == "__main__":
    print("page on :8610")
    ThreadingHTTPServer(("0.0.0.0", 8610), Handler).serve_forever()
