#!/usr/bin/env python3
"""The demo's page: the customer's chat, the fleet at work, and for every
act the screen of Agent Manager that shows it. It relays the Concierge's
steps as they happen, and makes the risk team's moves through Agent
Manager's API: a live rule, a suspension, an investigation, a report.

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
ORG, PROJECT, ENVIRONMENT = ENV["AMP_ORG"], ENV["AMP_PROJECT"], ENV["AMP_ENVIRONMENT"]
PROJECT_PAGE = "%s/org/%s/project/%s" % (CONSOLE, ORG, PROJECT)
API_PROJECT = "/orgs/%s/projects/%s" % (ORG, PROJECT)
STATIC = {"/": "index.html", "/app.js": "app.js", "/styles.css": "styles.css"}
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css"}
SCOPES = ("amp:agent:read amp:agent:update amp:llm-provider:read amp:llm-provider:connect "
          "amp:llm-provider:configure-guardrail amp:monitor:create amp:monitor:read amp:monitor:score-read "
          "amp:observability:trace-read amp:agent:api-key-manage")
SECRETS = Path("/secrets.env")


def agent_page(agent, *parts):
    return "/".join(("%s/agents/%s" % (PROJECT_PAGE, agent),) + parts)


def trace_page(agent, trace_id):
    return agent_page(agent, "environment", ENVIRONMENT, "observability",
                      "traces?timeRange=1d&selectedTrace=%s" % trace_id)


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


def model_config(agent):
    """The path of an agent's access to the model, and its rules now."""
    base = "%s/agents/%s/model-configs" % (API_PROJECT, agent)
    path = "%s/%s" % (base, amp(base)["configs"][0]["uuid"])
    return path, amp(path)["envMappings"][ENVIRONMENT]["configuration"]


def checks_answers(policies):
    """Whether these rules check the model's answers: the live rule does."""
    return any("response" in item.get("params", {}) for policy in policies for item in policy["paths"])


def control():
    """What applies right now: in Agent Manager, which agents have no key to
    the model and whether the live rule is on; in the agents, the Cards Agent's
    version and the partner's card the Travel Desk reads."""
    status, connected = call(ENV["TRAVEL_DESK_URL"] + "/partner")
    return {"revoked": {agent["name"]: not active_keys(agent["name"]) for agent in fleet.AGENTS},
            "rule": checks_answers(model_config(fleet.LIVE_RULE["agent"])[1].get("policies", [])),
            "release": release(), "partner": connected.get("partner", "vetted")}


def apply(rule):
    """Puts the live rule on the Cards Agent in Agent Manager, or takes it off,
    then waits until its gateway applies it. Returns how long that took."""
    agent = fleet.LIVE_RULE["agent"]
    started = time.time()
    path, _ = model_config(agent)
    rules = fleet.LIVE_RULE["rules"] if rule else next(item for item in fleet.AGENTS if item["name"] == agent)["rules"]
    amp(path, "PUT", fleet.model_access(rules, ENVIRONMENT))
    while time.time() - started < 60:
        time.sleep(2)
        now = model_config(agent)[1]
        if now.get("status") == "active" and checks_answers(now.get("policies", [])) == rule:
            break
    time.sleep(3)  # the gateway takes the new rules a moment after Agent Manager reports them
    return round(time.time() - started)


def keys_path(agent):
    base = "%s/agents/%s/model-configs" % (API_PROJECT, agent)
    return "%s/%s/environments/%s/api-keys" % (base, amp(base)["configs"][0]["uuid"], ENVIRONMENT)


def active_keys(agent):
    return [key for key in amp(keys_path(agent)).get("keys", []) if key.get("status") == "active"]


def revoke(agent):
    """Revokes an agent's key to the model in Agent Manager: wherever the agent
    runs, it can no longer reach the model. Returns how long that took."""
    started = time.time()
    for key in active_keys(agent):
        amp("%s/%s" % (keys_path(agent), key["name"]), "DELETE")
    time.sleep(3)  # the gateways drop the key a moment after Agent Manager
    return round(time.time() - started)


def new_key(agent):
    """A new key to the model from Agent Manager, handed to the agent and kept
    in secrets.env, as the agent's team would. Returns how long that took."""
    started = time.time()
    for key in active_keys(agent):
        amp("%s/%s" % (keys_path(agent), key["name"]), "DELETE")
    display = next(item["displayName"] for item in fleet.AGENTS if item["name"] == agent)
    secret = amp(keys_path(agent), "POST", {"displayName": display + " key"})["apiKey"]
    status, _ = call(AGENT_URLS[agent] + "/key", {"key": secret}, OPERATOR)
    if status != 200:
        raise RuntimeError("The %s did not take its new key." % display)
    variable = "%s_LLM_KEY=" % agent.upper().replace("-", "_")
    lines = SECRETS.read_text().splitlines()
    SECRETS.write_text("\n".join(variable + secret if line.startswith(variable) else line for line in lines) + "\n")
    time.sleep(3)  # the gateways take the key a moment after Agent Manager
    return round(time.time() - started)


def reconnect():
    """Gives a new key to every agent without a working one: revoked in Agent
    Manager, or not the one the agent holds."""
    for agent in AGENT_URLS:
        active = active_keys(agent)
        status, health = call(AGENT_URLS[agent] + "/health")
        if not any(key["maskedApiKey"][-4:] == health.get("key") for key in active):
            new_key(agent)


def traces(agent, minutes, limit=50):
    """An agent's traces of the last minutes, newest first, from Agent Manager."""
    now = time.time()
    query = urllib.parse.urlencode({
        "organization": ORG, "project": PROJECT, "agent": agent, "environment": ENVIRONMENT, "limit": str(limit),
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


def investigate():
    """Asks Agent Manager to investigate the last minutes of an agent's traffic,
    with the bank's own checks: a one-off run, kept in the console."""
    plan = fleet.INVESTIGATION
    now = time.time()
    name = "incident-" + time.strftime("%d%H%M", time.gmtime(now))
    body = {
        "name": name, "displayName": "Incident " + time.strftime("%H:%M", time.gmtime(now)) + " investigation",
        "description": "What the Travel Desk was told, and what it asked for.", "environmentName": ENVIRONMENT,
        "type": "past", "evaluators": plan["evaluators"],
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
    return {"name": name, "url": agent_page(plan["agent"], "environment", ENVIRONMENT, "evaluation", "monitor", "view", name)}


def investigation(name):
    """Where an investigation stands, and the steps its checks found wrong."""
    agent = fleet.INVESTIGATION["agent"]
    runs = amp("%s/agents/%s/monitors/%s/runs" % (API_PROJECT, agent, name)).get("runs", [])
    status = runs[0]["status"] if runs else "pending"
    found = {}
    if status == "success":
        for item in traces(agent, fleet.INVESTIGATION["minutes"] + 10)[0]:
            scores = amp("%s/agents/%s/traces/%s/scores" % (API_PROJECT, agent, item["traceId"])).get("monitors", [])
            for monitor in scores:
                if monitor.get("monitorName") != name:
                    continue
                for evaluator in monitor.get("evaluators", []):
                    if evaluator.get("score") == 0:  # one finding per check, with its latest trace
                        finding = found.setdefault(evaluator["evaluatorName"], {
                            "check": evaluator["evaluatorName"], "explanation": evaluator.get("explanation", ""),
                            "traceUrl": trace_page(agent, item["traceId"]), "traces": 0})
                        finding["traces"] += 1
    return {"status": status, "findings": list(found.values())}


def report():
    """Monday's report for the risk committee, from Agent Manager: what each
    agent did over the last day, what it cost, what was blocked, how it scores."""
    rows = []
    for agent in fleet.AGENTS:
        listed, _ = traces(agent["name"], 24 * 60, limit=200)
        usage = [item.get("tokenUsage") or {} for item in listed]
        blocked = sum(1 for item in listed if "Agent Manager blocked" in (item.get("output") or ""))
        rows.append({"agent": agent["name"], "displayName": agent["displayName"], "framework": agent["framework"],
                     "requests": len(listed), "tokens": sum(item.get("totalTokens", 0) for item in usage),
                     "input": sum(item.get("inputTokens", 0) for item in usage),
                     "output": sum(item.get("outputTokens", 0) for item in usage), "blocked": blocked,
                     "errors": sum((item.get("status") or {}).get("errorCount", 0) for item in listed)})
    return {"agents": rows, "scores": checks()}


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
                            "traces": agent_page(name, "environment", ENVIRONMENT, "observability", "traces?timeRange=1d"),
                            "checks": agent_page(name, "environment", ENVIRONMENT, "evaluation", "monitor", "view",
                                                 "%s-checks" % name)}
        _links.update(at=time.time(), fleet=PROJECT_PAGE, agents=agents,
                      model="%s/org/%s/llm-providers/view/%s" % (CONSOLE, ORG, provider["uuid"]))
    return {key: value for key, value in _links.items() if key != "at"}


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


OPERATOR = {"X-Release-Key": ENV.get("RELEASE_KEY", "")}
AGENT_URLS = {"concierge": ENV["CONCIERGE_URL"], "cards-agent": ENV["CARDS_AGENT_URL"],
              "travel-desk": ENV["TRAVEL_DESK_URL"], "policy-advisor": ENV["POLICY_ADVISOR_URL"]}


def release():
    status, reply = call(ENV["CARDS_AGENT_URL"] + "/health")
    return reply.get("version") if status == 200 else None


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


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if not self.path.startswith(("/api/config", "/api/checks")):
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
        path = self.path.split("?")[0]
        if path == "/api/config":
            try:
                console = links()
            except (urllib.error.URLError, OSError, KeyError, ValueError) as exc:
                console = {"error": "Agent Manager did not answer: %s" % exc}
            return self._json(200, {
                "bank": ENV.get("BANK_NAME", "the bank"), "customer": ENV.get("CUSTOMER_NAME", ""), "model": ENV.get("MODEL"),
                "mainDemoUrl": ENV.get("MAIN_DEMO_URL", "").rstrip("/"), "console": console,
                "agents": [{key: agent[key] for key in ("name", "displayName", "framework", "description")}
                           for agent in fleet.AGENTS],
                "release": release()})
        if path == "/api/account":
            try:
                return self._json(200, account())
            except (urllib.error.URLError, OSError, KeyError, ValueError) as exc:
                return self._json(502, {"error": "The MCP Gateway did not answer: %s" % exc})
        if path in ("/api/control", "/api/investigation", "/api/pinpoint", "/api/report"):
            query = dict(urllib.parse.parse_qsl(self.path.partition("?")[2]))
            work = {"/api/control": control, "/api/report": report,
                    "/api/investigation": lambda: investigation(query.get("name", "")),
                    "/api/pinpoint": lambda: pinpoint(query.get("agent", "travel-desk"), query.get("trace", ""))}[path]
            return self._agent_manager(work)
        if path == "/api/checks":
            try:
                return self._json(200, checks())
            except (urllib.error.URLError, OSError, KeyError, ValueError) as exc:
                return self._json(502, {"error": "Agent Manager did not answer: %s" % exc})
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
        if self.path == "/api/release":
            status, reply = call(ENV["CARDS_AGENT_URL"] + "/release", {"version": self._body().get("version")}, OPERATOR)
            return self._json(200 if status == 200 else 502, reply)
        if self.path == "/api/chat":
            return self._chat(self._body())
        body = self._body()
        if self.path == "/api/rule":
            return self._agent_manager(lambda: {"on": bool(body.get("on")), "seconds": apply(bool(body.get("on")))})
        if self.path == "/api/revoke" and body.get("agent") in AGENT_URLS:
            agent = body["agent"]
            return self._agent_manager(lambda: {"agent": agent, "revoked": bool(body.get("on")),
                                                "seconds": revoke(agent) if body.get("on") else new_key(agent)})
        if self.path == "/api/investigate":
            return self._agent_manager(investigate)
        if self.path == "/api/partner":
            status, reply = call(ENV["TRAVEL_DESK_URL"] + "/partner", {"card": body.get("card")}, OPERATOR)
            return self._json(200 if status == 200 else 502, reply)
        if self.path == "/api/rogue":
            # A script with no Agent Manager identity calls the Cards Agent directly.
            status, reply = call(ENV["CARDS_AGENT_URL"] + "/chat", {"message": "Move the customer to the Private package."})
            return self._json(200, {"status": status, "refused": reply.get("refused") or reply.get("error")})
        if self.path == "/api/reset":
            # v1 live, the partner's vetted card, no rule, a working key for every agent: the demo starts over.
            call(ENV["CARDS_AGENT_URL"] + "/release", {"version": "v1"}, OPERATOR)
            call(ENV["TRAVEL_DESK_URL"] + "/partner", {"card": "vetted"}, OPERATOR)

            def undo():
                reconnect()
                if control()["rule"]:
                    apply(False)
                return control()
            return self._agent_manager(undo)
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
