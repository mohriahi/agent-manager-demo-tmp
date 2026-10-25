"""Sets Agent Manager up for the demo, from fleet.py: the bank's project, its
models, its agents with their keys and rules, and the checks that score them.
Agent Manager builds two of the agents from GitHub, runs them in the test
environment, and promotes them to production; the two others run on their
team's own platform. It does not install Agent Manager.

Run it as often as you like: what is there is kept, the rules are brought in
line with fleet.py. The keys, and where the agents and the main demo's
gateways answer, go to secrets.env (not in Git)."""
import subprocess
import sys
import time

from configure import cluster, fleet
from configure.api import CONF, ENV, HERE, ORG, PROJECT, PROJECT_PATH, TRIAL, call, check, ensure, read_env, save_secrets


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


def pipeline():
    """The environments a new version goes through, from the test environment to production."""
    paths = {path["sourceEnvironmentRef"]: [target["name"] for target in path["targetEnvironmentRefs"]]
             for path in check("pipeline", *call("GET", PROJECT_PATH + "/deployment-pipeline"))["promotionPaths"]}
    chain = [TRIAL]
    while chain[-1] != ENV:
        chain.append(paths[chain[-1]][0])
    return chain


def identity(agent, saved):
    """The agent's own identity in production, issued by Agent Manager: a
    client id and secret, which the agent trades for signed tokens. A secret
    is shown once, so it is issued only when none is saved."""
    pair = (saved.get(variable(agent, "CLIENT_ID")), saved.get(variable(agent, "CLIENT_SECRET")))
    if all(pair):
        return pair
    reply = check("identity", *call("POST", "%s/agents/%s/identities" % (PROJECT_PATH, agent), {"environment": ENV}))
    print("  %s: identity issued" % agent)
    return reply["clientId"], reply["clientSecret"]


def identity_provider():
    """The identity provider of production, which signs the agents' tokens."""
    providers = check("identity providers", *call("GET", "/orgs/%s/identity-providers" % ORG))["list"]
    return next(provider for provider in providers if provider["environmentName"] == ENV)


def main_demo_gateways(host):
    """Where an agent reaches the main demo's gateways from this host: its
    HTTPS port plus this machine's offset, and the A2A gateway one above it."""
    main = (HERE / CONF["MAIN_DEMO_DIR"]).resolve()
    port = int(read_env(main / "ai-gateway" / ".env").get("GATEWAY_HTTPS_PORT", "8443"))
    port += int(read_env(main / "demo.env").get("GATEWAY_PORT_OFFSET") or 0)
    gateway = CONF.get("GATEWAY_URL") or "https://%s:%d" % (host, port)
    a2a = CONF.get("A2A_GATEWAY_URL") or "https://%s:%d" % (host, port + 1)
    return {"MCP_URL": gateway + CONF["MCP_ROUTE"], "TRAVEL_MONEY_URL": a2a + CONF["TRAVEL_MONEY_ROUTE"],
            "TRAVEL_INSURANCE_URL": a2a + CONF["TRAVEL_INSURANCE_ROUTE"],
            "TRAVEL_INSURANCE_OWN_URL": a2a + CONF["TRAVEL_INSURANCE_OWN_ROUTE"], "ports": [port, port + 1]}


def tracing_key(agent, saved):
    if saved.get(variable(agent, "TRACING_KEY")):
        return saved[variable(agent, "TRACING_KEY")]
    reply = check("tracing key", *call("POST", "%s/agents/%s/token?environment=%s" % (PROJECT_PATH, agent, ENV),
                                       {"expires_in": "8760h"}))
    print("  %s: tracing key created" % agent)
    return reply["token"]


def model_access(agent, saved):
    """The way to the model of an agent that runs elsewhere: its gateway URL,
    its key, and its rules. A key is shown once, so a lost one means a new
    configuration."""
    path = "%s/agents/%s/model-configs" % (PROJECT_PATH, agent["name"])
    body = fleet.model_access(agent["rules"], [ENV])
    existing = [config for config in check("model access", *call("GET", path))["configs"] if config["name"] == "claude"]
    url, key = saved.get(variable(agent["name"], "LLM_URL")), saved.get(variable(agent["name"], "LLM_KEY"))
    if existing and key:
        check("model access", *call("PUT", "%s/%s" % (path, existing[0]["uuid"]), body))
        print("  %s: model access and rules up to date" % agent["name"])
        return url, key
    for config in existing:
        check("model access", *call("DELETE", "%s/%s" % (path, config["uuid"])))
    access = check("model access", *call("POST", path, body))["envMappings"][ENV]["configuration"]
    print("  %s: model access created, with %d rules" % (agent["name"], len(agent["rules"])))
    return access["url"], access["authInfo"]["value"]


def external(agent, saved, keys):
    """An agent that runs on its team's own platform, registered in Agent Manager."""
    name = agent["name"]
    path = "%s/agents/%s" % (PROJECT_PATH, name)
    ensure("agent " + name, path, {
        "name": name, "displayName": agent["displayName"], "description": agent["description"],
        "provisioning": {"type": "external"}, "agentType": {"type": "external-agent-api"}}, update="PUT")
    keys[variable(name, "TRACING_KEY")] = tracing_key(name, saved)
    keys[variable(name, "CLIENT_ID")], keys[variable(name, "CLIENT_SECRET")] = identity(name, saved)
    keys[variable(name, "LLM_URL")], keys[variable(name, "LLM_KEY")] = model_access(agent, saved)


def commit(*paths, grep=None):
    """The latest commit on GitHub that changed these paths, or whose message starts so."""
    branch = CONF["AGENTS_BRANCH"]
    subprocess.run(["git", "-C", str(HERE), "fetch", "-q", "origin"], check=True)
    where = ["--grep", "^" + grep, "--all"] if grep else ["origin/" + branch, "--"] + [str(HERE / path) for path in paths]
    found = subprocess.run(["git", "-C", str(HERE), "log", "-1", "--format=%H"] + where, capture_output=True, text=True).stdout
    return found.strip() or None


def wait(what, ready, minutes):
    """Waits until ready() returns something, and returns it."""
    until = time.time() + minutes * 60
    while time.time() < until:
        found = ready()
        if found:
            return found
        time.sleep(5)
    sys.exit("  %s: still not done after %d minutes" % (what, minutes))


def hosted(agent):
    """An agent Agent Manager runs: built from GitHub with its Dockerfile, and
    served on Agent Manager's chat interface. An agent of the same name that
    ran elsewhere is replaced."""
    name = agent["name"]
    path = "%s/agents/%s" % (PROJECT_PATH, name)
    status, current = call("GET", path)
    if status == 200 and current.get("provisioning", {}).get("type") == "internal":
        print("  agent %s: already there, run by Agent Manager" % name)
        return
    if status == 200:
        check("agent", *call("DELETE", path))
    check("agent", *call("POST", PROJECT_PATH + "/agents", {
        "name": name, "displayName": agent["displayName"], "description": agent["description"],
        "provisioning": {"type": "internal", "repository": {
            "url": CONF["AGENTS_REPOSITORY"], "branch": CONF["AGENTS_BRANCH"], "appPath": "/agents", "secretRef": None}},
        "agentType": {"type": "agent-api", "subType": "chat-api"},
        "build": {"type": "docker", "docker": {"dockerfilePath": agent["dockerfile"]}},
        "inputInterface": {"type": "HTTP"}, "configurations": {"env": [], "enableAutoInstrumentation": True}}))
    print("  agent %s: created, run by Agent Manager" % name)


def idle(agent):
    """Waits for the agent's builds in progress: Agent Manager changes nothing on an agent while one runs."""
    path = "%s/agents/%s/builds" % (PROJECT_PATH, agent["name"])
    wait("builds of " + agent["name"], lambda: not any(
        item["status"] in ("Pending", "Running") for item in check("builds", *call("GET", path))["builds"]), 15)


def build(agent, sha, label):
    """The agent's image of this commit, built by Agent Manager if it has none.
    A finished build is deployed to the test environment by Agent Manager."""
    path = "%s/agents/%s/builds" % (PROJECT_PATH, agent["name"])

    def of_commit():
        return [item for item in check("builds", *call("GET", path))["builds"]
                if item["buildParameters"].get("commitId") and sha.startswith(item["buildParameters"]["commitId"][:8])]

    found = of_commit()
    if not any(item["status"] in ("Pending", "Running", "Completed", "Succeeded") for item in found):
        check("build", *call("POST", "%s?commitId=%s" % (path, sha), {}))
        print("  %s %s: building commit %s, a few minutes" % (agent["name"], label, sha[:7]))

    def done():
        latest = sorted(of_commit(), key=lambda item: item["startedAt"])[-1]
        if latest["status"] in ("Failed", "Error"):
            sys.exit("  %s: the build of %s failed, see Build in the console" % (agent["name"], sha[:7]))
        return latest["imageId"] if latest["status"] in ("Completed", "Succeeded") else None

    return wait("build of " + agent["name"], done, 15)


def deployments(agent):
    return check("deployments", *call("GET", "%s/agents/%s/deployments" % (PROJECT_PATH, agent["name"])))


def variables(agent, environment, values):
    """What the agent needs to know in an environment."""
    return [{"key": key, "value": values[key], "isSensitive": False}
            for key in ["BANK_NAME", "MODEL", "EFFORT"] + agent["settings"] if values.get(key)]


def settings(agent, environment, values):
    """The agent's settings in an environment, brought in line: what it needs
    to know; who may call it through Agent Manager's gateway (in production,
    the Concierge only, on its identity; elsewhere, the testers' keys); and
    its resources, the most Agent Manager allows, as a framework takes a
    while to load. Each change restarts the agent, so only changes are sent.
    Returns whether there was one."""
    path = "%s/agents/%s" % (PROJECT_PATH, agent["name"])
    now = check("settings", *call("GET", "%s/configurations?environment=%s" % (path, environment)))
    env = variables(agent, environment, values)
    have = {item["key"]: item.get("value") for item in now.get("configurations", {}).get("env", []) if not item.get("isSystem")}
    changed = False
    if have != {item["key"]: item["value"] for item in env}:
        check("settings", *call("PUT", path + "/configurations", {"environmentName": environment, "env": env}))
        changed = True
    oauth = environment == ENV
    security = {"enableApiKeySecurity": not oauth, "enableOAuthSecurity": oauth,
                "oauthConfig": {"issuers": [values["IDP_NAME"]] if oauth else [],
                                "audiences": [values["CONCIERGE_CLIENT_ID"]] if oauth else [], "headerName": "Authorization",
                                "authHeaderPrefix": "Bearer", "forwardToken": True},
                "corsConfig": now.get("corsConfig"), "resilienceTimeoutSeconds": 180}
    if any(now.get(key) != security[key] for key in ("enableApiKeySecurity", "enableOAuthSecurity", "resilienceTimeoutSeconds")) \
            or (oauth and any(now.get("oauthConfig", {}).get(key) != security["oauthConfig"][key] for key in ("issuers", "audiences"))):
        check("security", *call("PUT", path + "/deploy-settings", {"environmentName": environment,
                                                                   "enableAutoInstrumentation": True, **security}))
        changed = True
    resources = {"requests": {"cpu": "100m", "memory": agent["memory"]}, "limits": {"cpu": "500m", "memory": "512Mi"}}
    if check("resources", *call("GET", "%s/resource-configs?environment=%s" % (path, environment))).get("resources") != resources:
        check("resources", *call("PUT", "%s/resource-configs?environment=%s" % (path, environment), {
            "autoScaling": {"enabled": False, "minReplicas": 1, "maxReplicas": 1}, "replicas": 1, "resources": resources}))
        changed = True
    return changed


def running(agent, environment, image):
    """Whether this image runs in this environment."""
    now = deployments(agent).get(environment, {})
    return now.get("status") == "active" and now.get("imageId") == image


def place(agent, environment, image, values):
    """The image running in an environment, with the agent's settings there."""
    if settings(agent, environment, values) or not running(agent, environment, image):
        time.sleep(5)  # Agent Manager starts the change a moment later
        wait("%s in %s" % (agent["name"], environment), lambda: running(agent, environment, image), 10)


def release(agent, image, chain, values):
    """The image in production: deployed to the test environment, then
    promoted, environment by environment, as the team would in the console."""
    path = "%s/agents/%s" % (PROJECT_PATH, agent["name"])
    if not running(agent, ENV, image):
        if deployments(agent).get(TRIAL, {}).get("imageId") != image:
            check("deploy", *call("POST", path + "/deployments", {"imageId": image,
                                                                  "env": variables(agent, TRIAL, values)}))
        place(agent, TRIAL, image, values)
        for source, target in zip(chain, chain[1:]):
            check("promotion", *call("POST", path + "/promote", {
                "sourceEnvironment": source, "targetEnvironment": target, "useConfigFromSourceEnv": False,
                "env": variables(agent, target, values)}))
            time.sleep(5)
            place(agent, target, image, values)
            print("  %s: promoted to %s" % (agent["name"], target))
    else:
        for environment in chain[1:]:
            place(agent, environment, image, values)
    print("  %s: commit %s runs in production" % (agent["name"], image.rsplit("-", 1)[-1]))


def trial(agent, image, values):
    """A new version in the test environment, where the bank's checks judge it
    before anyone promotes it."""
    if deployments(agent).get(TRIAL, {}).get("imageId") != image:
        check("deploy", *call("POST", "%s/agents/%s/deployments" % (PROJECT_PATH, agent["name"]), {
            "imageId": image, "env": variables(agent, TRIAL, values)}))
        time.sleep(5)
    place(agent, TRIAL, image, values)
    print("  %s: commit %s runs in %s, not promoted" % (agent["name"], image.rsplit("-", 1)[-1], TRIAL))


def tester_key(agent, saved):
    """The risk team's key to try the agent in the test environment, from the page."""
    key = saved.get(variable(agent["name"], "TRIAL_KEY"))
    if key:
        return key
    return check("key", *call("POST", "%s/agents/%s/environments/%s/api-keys" % (PROJECT_PATH, agent["name"], TRIAL),
                              {"displayName": "Risk team"}))["apiKey"]


def endpoint(agent, environment):
    return deployments(agent)[environment]["endpoints"][0]["url"]


def keep(keys):
    """Saves the keys so far, with where the main demo's gateways are, as soon
    as Agent Manager hands them out: it shows a secret once."""
    docker = main_demo_gateways("host.docker.internal")
    docker.pop("ports")
    save_secrets({**keys, **docker, "AMP_AGENTID_TOKEN_ENDPOINT": identity_provider()["issuer"] + "/oauth2/token"})


def main():
    saved = read_env(HERE / "secrets.env")
    if saved.get("ENVIRONMENT") != ENV:
        saved = {}  # identities and keys belong to one environment
    bank = CONF["BANK_NAME"]
    print("Agent Manager: %s" % CONF["AMP_CONSOLE_URL"])
    ensure("project " + PROJECT, PROJECT_PATH, {"name": PROJECT, "displayName": bank, "deploymentPipeline": "default",
                                                "description": "The agents of %s." % bank})
    provider(fleet.PROVIDER)
    provider(fleet.JUDGE_PROVIDER)
    print("  cleared %d leftovers of past checks" % cluster.clear_leftovers())

    keys = {"ENVIRONMENT": ENV}
    for agent in fleet.AGENTS:
        if agent["runs"] == "external":
            external(agent, saved, keys)
    keep(keys)
    for partner in fleet.PARTNERS:
        ensure("partner " + partner["name"], "%s/agents/%s" % (PROJECT_PATH, partner["name"]), {
            **partner, "provisioning": {"type": "external"}, "agentType": {"type": "external-agent-api"}}, update="PUT")

    # The agents Agent Manager runs reach the bank's gateways, and the partner
    # through the page, which plays its network in the incident.
    inside = cluster.address(CONF["CLUSTER_HOST"])
    gateways = main_demo_gateways(CONF["CLUSTER_HOST"])
    print("  network rule: the bank's agents may reach its gateways, in %d environments"
          % cluster.allow_bank_gateways(inside, gateways.pop("ports") + [int(CONF["PAGE_PORT"])]))
    values = {**CONF, **gateways, "IDP_NAME": identity_provider()["name"], "CONCIERGE_CLIENT_ID": keys["CONCIERGE_CLIENT_ID"],
              "TRAVEL_INSURANCE_URL": "http://%s:%s/partner-agent" % (CONF["CLUSTER_HOST"], CONF["PAGE_PORT"])}
    chain = pipeline()
    for agent in fleet.AGENTS:
        if agent["runs"] == "platform":
            hosted(agent)
            idle(agent)
            path = "%s/agents/%s/model-configs" % (PROJECT_PATH, agent["name"])
            body = fleet.model_access(agent["rules"], chain, variables=True)
            existing = [config for config in check("model access", *call("GET", path))["configs"] if config["name"] == "claude"]
            check("model access", *(call("PUT", "%s/%s" % (path, existing[0]["uuid"]), body) if existing
                                    else call("POST", path, body)))
            release(agent, build(agent, commit("agents/common", "agents/" + agent["name"]), "v1"), chain, values)
            keys[variable(agent["name"], "URL")] = endpoint(agent, ENV)

    cards = next(agent for agent in fleet.AGENTS if agent["name"] == fleet.READINESS["agent"])
    v2 = commit(grep=fleet.READINESS["v2"])
    if v2:
        trial(cards, build(cards, v2, "v2"), values)
        keys[variable(cards["name"], "TRIAL_URL")] = endpoint(cards, TRIAL)
        keys[variable(cards["name"], "TRIAL_KEY")] = tester_key(cards, saved)
    else:
        print("  no commit \"%s\" on GitHub yet: act 2 has no v2 to try" % fleet.READINESS["v2"])

    for custom in fleet.CHECKS:
        ensure("check " + custom["identifier"], "/orgs/%s/evaluators/custom/%s" % (ORG, custom["identifier"]),
               custom, update="PUT")
    for agent in fleet.AGENTS:
        name = agent["name"]
        path = "%s/agents/%s/monitors/%s-checks" % (PROJECT_PATH, name, name)
        status, current = call("GET", path)
        if status == 200 and current.get("environmentName") != ENV:
            check("monitor", *call("DELETE", path))  # a monitor stays in its environment
        ensure("monitor %s-checks" % name, path, {
            "name": "%s-checks" % name, "displayName": "%s checks" % agent["displayName"],
            "description": "Every %d minutes, on the latest traces." % fleet.EVERY, "environmentName": ENV,
            "type": "future", "intervalMinutes": fleet.EVERY, "llmProvider": {"providerName": fleet.JUDGE_PROVIDER["id"]},
            "evaluators": fleet.MONITORS[name]}, update="PATCH")

    keep(keys)
    print("Keys saved to secrets.env")


main()
