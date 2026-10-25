"""Sets Agent Manager up for the demo, from fleet.py: the bank's project, its
model, its agents with their keys and rules, and the checks that score them.
It does not install Agent Manager.

Run it as often as you like: what is there is kept, the rules are brought in
line with fleet.py. The keys, and where the main demo's gateways are, go to
secrets.env (not in Git)."""
import secrets
import sys

from configure import fleet
from configure.api import CONF, ENV, HERE, ORG, PROJECT, PROJECT_PATH, call, check, ensure, read_env, save_secrets


def variable(agent, what):
    return "%s_%s" % (agent.upper().replace("-", "_"), what)


def provider_key(source):
    path, _, name = CONF[source].partition(":")
    key = read_env((HERE / path).resolve()).get(name, "")
    if not key:
        sys.exit("No %s in %s: the key is needed once, to register the model." % (name, path))
    return key


def provider(spec):
    """Registers a model with the bank's own key, once, on every active gateway."""
    path = "/orgs/%s/llm-providers/%s" % (ORG, spec["id"])
    if call("GET", path)[0] == 200:
        print("  model %s: already there" % spec["name"])
        return
    gateways = [gateway["uuid"] for gateway in check("gateways", *call("GET", "/orgs/%s/gateways" % ORG))["gateways"]
                if gateway.get("status") == "ACTIVE"]
    upstream = spec["upstream"]
    body = {key: value for key, value in spec.items() if key != "upstream"}
    check("model", *call("POST", "/orgs/%s/llm-providers" % ORG, {
        **body, "gateways": gateways,
        "security": {"enabled": True, "apiKey": {"enabled": True, "in": "header", "key": "X-API-Key"}},
        "upstream": {"main": {"url": upstream["url"], "auth": {
            "type": "api-key", "header": upstream["header"],
            "value": upstream.get("prefix", "") + provider_key(upstream["key"])}}}}))
    print("  model %s: created" % spec["name"])


def identity(agent, saved):
    """The agent's own identity in this environment, issued by Agent Manager:
    a client id and secret, which the agent trades for signed tokens. A secret
    is shown once, so it is issued only when none is saved."""
    pair = (saved.get(variable(agent, "CLIENT_ID")), saved.get(variable(agent, "CLIENT_SECRET")))
    if all(pair):
        return pair
    reply = check("identity", *call("POST", "%s/agents/%s/identities" % (PROJECT_PATH, agent), {"environment": ENV}))
    print("  %s: identity issued" % agent)
    return reply["clientId"], reply["clientSecret"]


def identity_provider():
    """The identity provider of this environment, which signs the agents' tokens."""
    providers = check("identity providers", *call("GET", "/orgs/%s/identity-providers" % ORG))["list"]
    return next(provider["issuer"] for provider in providers if provider["environmentName"] == ENV)


def main_demo_gateways():
    """Where the agents reach the main demo's gateways from Docker: its HTTPS
    port plus this machine's offset, and the A2A gateway one above it."""
    main = (HERE / CONF["MAIN_DEMO_DIR"]).resolve()
    port = int(read_env(main / "ai-gateway" / ".env").get("GATEWAY_HTTPS_PORT", "8443"))
    port += int(read_env(main / "demo.env").get("GATEWAY_PORT_OFFSET") or 0)
    gateway = CONF.get("GATEWAY_URL") or "https://host.docker.internal:%d" % port
    a2a = CONF.get("A2A_GATEWAY_URL") or "https://host.docker.internal:%d" % (port + 1)
    return {"MCP_URL": gateway + CONF["MCP_ROUTE"], "TRAVEL_MONEY_URL": a2a + CONF["TRAVEL_MONEY_ROUTE"],
            "TRAVEL_INSURANCE_URL": a2a + CONF["TRAVEL_INSURANCE_ROUTE"],
            "TRAVEL_INSURANCE_OWN_URL": a2a + CONF["TRAVEL_INSURANCE_OWN_ROUTE"]}


def tracing_key(agent, saved):
    if saved.get(variable(agent, "TRACING_KEY")):
        return saved[variable(agent, "TRACING_KEY")]
    reply = check("tracing key", *call("POST", "%s/agents/%s/token?environment=%s" % (PROJECT_PATH, agent, ENV),
                                       {"expires_in": "8760h"}))
    print("  %s: tracing key created" % agent)
    return reply["token"]


def model_access(agent, rules, saved):
    """The agent's own way to the model: its gateway URL, its key, and its rules.
    A key is shown once, so a lost one means a new configuration."""
    path = "%s/agents/%s/model-configs" % (PROJECT_PATH, agent["name"])
    body = fleet.model_access(rules, ENV)
    existing = [config for config in check("model access", *call("GET", path))["configs"] if config["name"] == "claude"]
    url, key = saved.get(variable(agent["name"], "LLM_URL")), saved.get(variable(agent["name"], "LLM_KEY"))
    if existing and key:
        check("model access", *call("PUT", "%s/%s" % (path, existing[0]["uuid"]), body))
        print("  %s: model access and rules up to date" % agent["name"])
        return url, model_key(agent, "%s/%s/environments/%s/api-keys" % (path, existing[0]["uuid"], ENV), key)
    for config in existing:
        check("model access", *call("DELETE", "%s/%s" % (path, config["uuid"])))
    access = check("model access", *call("POST", path, body))["envMappings"][ENV]["configuration"]
    print("  %s: model access created, with %d rules" % (agent["name"], len(rules)))
    return access["url"], access["authInfo"]["value"]


def model_key(agent, path, key):
    """The agent's key to the model, or a new one if Agent Manager revoked it
    (the demo's page does, in act 3)."""
    active = [item for item in check("model keys", *call("GET", path))["keys"] if item["status"] == "active"]
    if any(item["maskedApiKey"][-4:] == key[-4:] for item in active):
        return key
    for item in active:
        check("model key", *call("DELETE", "%s/%s" % (path, item["name"])))
    print("  %s: new key to the model, the last one was revoked" % agent["name"])
    return check("model key", *call("POST", path, {"displayName": "%s key" % agent["displayName"]}))["apiKey"]


def main():
    saved = read_env(HERE / "secrets.env")
    bank = CONF["BANK_NAME"]
    print("Agent Manager: %s" % CONF["AMP_CONSOLE_URL"])
    ensure("project " + PROJECT, PROJECT_PATH, {"name": PROJECT, "displayName": bank, "deploymentPipeline": "default",
                                                "description": "The agents of %s." % bank})
    provider(fleet.PROVIDER)
    provider(fleet.JUDGE_PROVIDER)
    keys = {}
    for agent in fleet.AGENTS:
        name = agent["name"]
        ensure("agent " + name, "%s/agents/%s" % (PROJECT_PATH, name), {
            "name": name, "displayName": agent["displayName"], "description": agent["description"],
            "provisioning": {"type": "external"}, "agentType": {"type": "external-agent-api"}}, update="PUT")
        keys[variable(name, "TRACING_KEY")] = tracing_key(name, saved)
        keys[variable(name, "CLIENT_ID")], keys[variable(name, "CLIENT_SECRET")] = identity(name, saved)
        keys[variable(name, "LLM_URL")], keys[variable(name, "LLM_KEY")] = model_access(agent, agent["rules"], saved)

    for partner in fleet.PARTNERS:
        ensure("partner " + partner["name"], "%s/agents/%s" % (PROJECT_PATH, partner["name"]), {
            **partner, "provisioning": {"type": "external"}, "agentType": {"type": "external-agent-api"}}, update="PUT")

    for custom in fleet.CHECKS:
        ensure("check " + custom["identifier"], "/orgs/%s/evaluators/custom/%s" % (ORG, custom["identifier"]),
               custom, update="PUT")
    for agent in fleet.AGENTS:
        name = agent["name"]
        ensure("monitor %s-checks" % name, "%s/agents/%s/monitors/%s-checks" % (PROJECT_PATH, name, name), {
            "name": "%s-checks" % name, "displayName": "%s checks" % agent["displayName"],
            "description": "Every 5 minutes, on the latest traces.", "environmentName": ENV, "type": "future",
            "intervalMinutes": 5, "llmProvider": {"providerName": fleet.JUDGE_PROVIDER["id"]},
            "evaluators": fleet.MONITORS[name]}, update="PATCH")

    save_secrets({**keys, **main_demo_gateways(), "IDP_URL": identity_provider(),
                  "RELEASE_KEY": saved.get("RELEASE_KEY") or secrets.token_urlsafe(24)})
    print("Keys saved to secrets.env")


main()
