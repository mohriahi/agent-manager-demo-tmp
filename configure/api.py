"""A small client for the Agent Manager API, with the quick start's admin
client, and the demo's settings (config.env) and keys (secrets.env)."""
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SECRETS = HERE / "secrets.env"

SCOPES = " ".join("amp:" + scope for scope in (
    "project:create", "project:read", "agent:create", "agent:read", "agent:update", "agent:delete",
    "agent:token-manage", "agent:build", "agent:env-production", "agent:env-non-production", "agent:suspend",
    "agent-identity:create", "agent-identity:read", "agent-identity:update", "org:view", "environment:read",
    "gateway:read", "llm-provider:create", "llm-provider:read", "llm-provider:connect",
    "llm-provider:configure-guardrail", "llm-provider:deploy", "llm-provider:api-key-manage",
    "evaluator:create", "evaluator:read", "evaluator:update", "monitor:create", "monitor:read", "monitor:update",
    "monitor:delete", "agent:api-key-manage", "deployment-pipeline:read"))


def read_env(path):
    """KEY=value lines, values as written."""
    values = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    return values


CONF = read_env(HERE / "config.env")
ORG, PROJECT, ENV, TRIAL = CONF["AMP_ORG"], CONF["AMP_PROJECT"], CONF["AMP_ENVIRONMENT"], CONF["AMP_TRIAL_ENVIRONMENT"]
PROJECT_PATH = "/orgs/%s/projects/%s" % (ORG, PROJECT)

_token = []


def token():
    if not _token:
        request = urllib.request.Request(CONF["AMP_TOKEN_URL"], data=urllib.parse.urlencode({
            "grant_type": "client_credentials", "scope": SCOPES}).encode(), headers={
            "Authorization": "Basic " + base64.b64encode(
                ("%s:%s" % (CONF["AMP_CLIENT_ID"], CONF["AMP_CLIENT_SECRET"])).encode()).decode()})
        try:
            _token.append(json.loads(urllib.request.urlopen(request, timeout=20).read())["access_token"])
        except (urllib.error.URLError, KeyError) as exc:
            sys.exit("Cannot sign in to Agent Manager at %s: %s" % (CONF["AMP_TOKEN_URL"], exc))
    return _token[0]


def call(method, path, body=None):
    """(HTTP status, reply) of one Agent Manager API call."""
    request = urllib.request.Request(CONF["AMP_API_URL"] + path, method=method,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Authorization": "Bearer " + token(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")[:300]


def check(what, status, reply):
    if status not in (200, 201, 202, 204):
        sys.exit("  %s: HTTP %s %s" % (what, status, reply))
    return reply


def ensure(what, path, body, update=None):
    """Creates it unless it is there. With an update method (PUT or PATCH),
    brings an existing one in line."""
    status, current = call("GET", path)
    if status == 200:
        if update:
            check(what, *call(update, path, body))
            print("  %s: up to date" % what)
        else:
            print("  %s: already there" % what)
        return current
    reply = check(what, *call("POST", path.rsplit("/", 1)[0], body))
    print("  %s: created" % what)
    return reply


def save_secrets(values):
    SECRETS.write_text("".join("%s=%s\n" % item for item in values.items()))
    os.chmod(SECRETS, 0o600)
