#!/usr/bin/env python3
"""The demo's page: the customer's chat, the live map of the agents, and the
switch between the Cards Agent's versions. It relays the Assistant's steps as
they happen and links each answer to its traces in Agent Manager.

Python standard library only, so the stock Python image runs it as is.
"""
import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENV = os.environ
ASSISTANT = ENV["ASSISTANT_URL"]
CARDS_AGENT = ENV["CARDS_AGENT_URL"]
CONSOLE = ENV["AMP_CONSOLE_URL"].rstrip("/")
PROJECT_PATH = "/org/%s/project/%s" % (ENV["AMP_ORG"], ENV["AMP_PROJECT"])
STATIC = {"/": "index.html", "/app.js": "app.js", "/styles.css": "styles.css"}
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css"}


def trace_url(agent, trace_id):
    """An agent's trace in the Agent Manager console."""
    return "%s%s/agents/%s/environment/%s/observability/traces?timeRange=1d&selectedTrace=%s" % (
        CONSOLE, PROJECT_PATH, agent, ENV["AMP_ENVIRONMENT"], trace_id)


def call(url, body=None, headers=None, timeout=10):
    """(HTTP status, JSON reply) of one call to an agent."""
    request = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as exc:
        return exc.code, {"error": exc.read().decode("utf-8", "replace")[:200]}
    except (urllib.error.URLError, OSError) as exc:
        return 0, {"error": str(exc)}


MONITOR = "cards-agent-checks"
_token = {"value": None, "until": 0}


def amp(path):
    """One read from the Agent Manager API, with the quick start's admin client."""
    if time.time() > _token["until"]:
        request = urllib.request.Request(ENV["AMP_TOKEN_URL"], data=urllib.parse.urlencode({
            "grant_type": "client_credentials", "scope": "amp:monitor:read amp:monitor:score-read"}).encode(),
            headers={"Authorization": "Basic " + base64.b64encode(
                ("%s:%s" % (ENV["AMP_CLIENT_ID"], ENV["AMP_CLIENT_SECRET"])).encode()).decode()})
        reply = json.loads(urllib.request.urlopen(request, timeout=10).read())
        _token.update(value=reply["access_token"], until=time.time() + reply.get("expires_in", 600) - 60)
    request = urllib.request.Request(ENV["AMP_API_URL"] + "/orgs/%s/projects/%s%s" % (
        ENV["AMP_ORG"], ENV["AMP_PROJECT"], path), headers={"Authorization": "Bearer " + _token["value"]})
    return json.loads(urllib.request.urlopen(request, timeout=10).read())


def checks():
    """Agent Manager's latest check of the Cards Agent: each evaluator's score."""
    base = "/agents/cards-agent/monitors/" + MONITOR
    monitor = amp(base)
    # The latest run that scored something: a run with no traffic in its window has no score.
    latest, scores = None, []
    for run in [run for run in amp(base + "/runs").get("runs", []) if run.get("status") == "success"][:6]:
        scores = amp("%s/runs/%s/scores" % (base, run["id"])).get("evaluators", [])
        if scores:
            latest = run
            break
    return {
        "monitorUrl": "%s%s/agents/cards-agent/environment/%s/evaluation/monitor/view/%s" % (
            CONSOLE, PROJECT_PATH, ENV["AMP_ENVIRONMENT"], monitor.get("id")),
        "every": monitor.get("intervalMinutes"), "nextRun": monitor.get("nextRunTime"),
        "lastRun": latest and latest.get("completedAt"),
        "evaluators": [{"name": item["evaluatorName"], "score": item.get("aggregations", {}).get("mean"),
                        "traces": item.get("count", 0) - item.get("skippedCount", 0)} for item in scores],
    }


def release():
    status, reply = call(CARDS_AGENT + "/health")
    return reply.get("version") if status == 200 else None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if not self.path.startswith("/api/config"):
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
            return self._json(200, {
                "bank": ENV.get("BANK_NAME") or "the bank",
                "mainDemoUrl": ENV.get("MAIN_DEMO_URL", "").rstrip("/"),
                "console": {"project": CONSOLE + PROJECT_PATH,
                            "assistant": CONSOLE + PROJECT_PATH + "/agents/assistant",
                            "cardsAgent": CONSOLE + PROJECT_PATH + "/agents/cards-agent"},
                "release": release()})
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
            version = self._body().get("version")
            status, reply = call(CARDS_AGENT + "/release", {"version": version},
                                 {"X-Release-Key": ENV.get("RELEASE_KEY", "")})
            return self._json(200 if status == 200 else 502, reply)
        if self.path == "/api/chat":
            return self._chat(self._body())
        self._json(404, {"error": "not found"})

    def _chat(self, body):
        """Relays the Assistant's steps as they happen, each with the link to
        its trace in Agent Manager once it has one."""
        request = urllib.request.Request(ASSISTANT + "/chat/stream", data=json.dumps({
            "message": str(body.get("message", ""))[:2000], "session_id": str(body.get("session", "demo"))[:100],
        }).encode(), headers={"Content-Type": "application/json"})
        try:
            upstream = urllib.request.urlopen(request, timeout=180)
        except (urllib.error.URLError, OSError) as exc:
            return self._json(502, {"error": "the Assistant does not answer: %s" % exc})
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        with upstream:
            for line in upstream:
                if not line.startswith(b"data:"):
                    continue
                event = json.loads(line[5:])
                if event.get("type") == "answer" and event.get("traceId"):
                    event["traceUrl"] = trace_url("assistant", event["traceId"])
                if event.get("to") == "Cards Agent" and event.get("traceId"):
                    event["traceUrl"] = trace_url("cards-agent", event["traceId"])
                self.wfile.write(b"data: %s\n\n" % json.dumps(event).encode())
                self.wfile.flush()


if __name__ == "__main__":
    print("page on :8610")
    ThreadingHTTPServer(("0.0.0.0", 8610), Handler).serve_forever()
