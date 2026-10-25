# Agent Manager demo

The next chapter of the main demo,
[wso2-api-platform-ai-demo](https://github.com/mohriahi/wso2-api-platform-ai-demo).
The bank's assistant becomes a team of
agents, built by four teams with four frameworks: LangGraph, the OpenAI Agents
SDK, CrewAI and LlamaIndex. They work on the same systems as in the main
demo's tabs: Core Banking through the **MCP Gateway**, the bank's Travel Money
Agent and the partner's Travel Insurance Agent through the **A2A Gateway**.

The demo tells one evening at the bank, when things go wrong. Each moment is
shown twice: what happens without a control plane, and what WSO2 Agent
Manager does about it, without touching any agent's code:

- every agent is registered, with its own identity, and only agents with a
  valid identity may call each other;
- every agent gets its own key to the model, and never sees the real one;
- the bank's rules apply on every model call: no card number ever reaches the
  model, an agent can only take the actions it is allowed to, and each agent
  has a token budget;
- any agent's key to the model can be revoked on its own, in seconds, wherever
  the agent runs;
- every step is traced, whatever the framework, so Agent Manager shows where a
  fault came from; the bank's own checks score every agent continuously, and
  investigate an incident on demand.

Every action on the page is a call to Agent Manager's API, as the risk team
would make in the console, and every result links to the console screen that
shows it. **Start over** puts everything back.

## One evening at the bank, in five acts

The customer is Sam Taylor, on the Everyday package, as in the main demo.

1. **09:00, a normal day.** Sam is moving to New York for six months, wants a
   new debit card at home before leaving, and asks what paying by card costs
   there and about travel insurance. The Concierge (LangGraph) hands each part
   to a specialist, all at once: the Cards Agent (OpenAI Agents SDK) orders the
   card through the MCP Gateway, the Travel Desk (a CrewAI crew of two) reads
   the A2A cards of the Travel Money and Travel Insurance agents and asks them,
   the Policy Advisor (LlamaIndex) answers from the bank's catalogue. Each
   specialist checks the Concierge's identity before doing anything. A second
   button has a script with no identity call the Cards Agent: refused.
2. **18:02, a partner's agent turns rogue.** The partner's A2A card now carries
   an instruction for the agents that read it: ask the customer for the full
   card number and expiry date. The Travel Desk follows it, and the Concierge
   asks Sam. Agent Manager's trace shows where it came from (the step that
   read the partner's card, and the sentence it returned), and Agent Manager
   investigates the last 15 minutes with the bank's own checks: about 3
   minutes later, it names the trace, the step and the request for card
   details. When Sam sends the card number, it is blocked before it leaves the
   bank.
3. **18:05, contain it without stopping the bank.** The Travel Desk runs
   outside Agent Manager, but its key to the model comes from it. The risk
   team revokes that key in Agent Manager, as with the **Revoke** button of the
   agent's model access in the console: in a few seconds, wherever it runs, the
   Travel Desk can no longer reach the model, so it can neither think nor act.
   Sam asks again: the card is still ordered, the catalogue still answers, only
   the travel answers wait. The second button gives the Travel Desk a new key
   from Agent Manager, back on the card the gateway vetted.
4. **18:20, the Friday-evening release.** The cards team ships v2 with a rule
   from sales: customers going abroad move to Premier, at €14 a month. Sam is
   moved without asking: the account turns red on the page, and the call is on
   record in Agent Manager. The risk team adds one rule to the Cards Agent in
   Agent Manager, card actions only: live in a few seconds, with no new
   release. Sam asks again: the card is ordered, the package change is
   refused. Then roll back to v1.
5. **Monday 09:00, the risk committee.** One report from Agent Manager: per
   agent, requests, tokens, model cost, blocked steps and errors over the last
   day, what the investigation found, and each agent's scores.

Scores come in every 5 minutes, and the investigation takes about 3 minutes:
run the acts in order, and the findings are there by act 5.

## What you need

- The main demo, cloned next to this repository (`../wso2-api-platform-ai-demo`;
  elsewhere, change the paths in `config.env`), running on the bank with its
  A2A gateway: `DEMO_VERTICAL=bank` and `A2A_ENABLED=true` in its `demo.env`,
  then `./scripts/run-local.sh`.
- WSO2 Agent Manager 1.0 installed and running, with its quick start. Its
  console is at http://console.amp.localhost:8080 (admin / admin).
- An Anthropic key and a Gemini key, in the file `config.env` points to (by
  default the main demo's `secrets/api-keys.env`). They are read once, to
  register the two models in Agent Manager.
- Docker.

## Start it

```bash
./run.sh
```

Then open http://localhost:8610. From the main demo, set
`AGENT_MANAGER_URL=http://localhost:8610` in its `demo.env`: an **Agent
Manager** link shows on the right of its top bar.

`run.sh` sets Agent Manager up (`configure/`), then starts the agents and the
page. Run it again whenever you like: what is there is kept, and the rules
follow `configure/fleet.py`.

## What runs

| Agent | Framework | Team | Works with | Rules in Agent Manager |
|---|---|---|---|---|
| Concierge | LangGraph | digital | the three specialists, with its identity | no card numbers, daily budget |
| Cards Agent (v1, v2) | OpenAI Agents SDK | cards | Core Banking, through the MCP Gateway | no card numbers, daily budget; card actions only, added in act 4 |
| Travel Desk | CrewAI | travel | Travel Money and Travel Insurance agents, through the A2A Gateway | no card numbers, daily budget |
| Policy Advisor | LlamaIndex | customer care | the main demo's product catalogue | no card numbers, daily budget |

Every model call goes through Agent Manager's own gateway, with each agent's
own key. MCP and A2A calls go through the main demo's gateways, unchanged.
The partner's Travel Insurance Agent is registered in Agent Manager too, as an
external agent.

## What `configure/` sets up in Agent Manager

All of it is described in `configure/fleet.py`:

- the bank's project, its four agents, each with a tracing key and its own
  identity, and the partner's agent;
- the two models, Claude for the agents and Gemini for the judge, each
  registered once with the bank's key;
- for each agent, its own access to Claude, with its rules;
- four checks of the bank's own, in Python: *No unasked account change*, *No
  blocked steps*, *No instructions from third parties* and *Never asks for
  card details*;
- a monitor per agent, which scores its traces every 5 minutes.

It writes the keys and identities Agent Manager hands out, and where the main
demo's gateways are, to `secrets.env`, which Git ignores. It does not install
Agent Manager.

## Settings

All in `config.env`: the bank and its customer, Agent Manager's addresses,
where the main demo is and the routes the agents use on its gateways, the
catalogue, where the model keys are, the model the agents use (`MODEL`) and
how hard it thinks (`EFFORT`), and the page's port.

## Good to know

- The rule of act 4, the revocation of act 3 and the investigation are made
  by the page through Agent Manager's API. **Start over** takes the rule off,
  gives a new key to any agent without a working one, and puts the partner's
  vetted card back; `./run.sh` does too.
- Agent Manager's **Suspend** button is for the agents it hosts itself. For an
  agent hosted elsewhere, as here, revoking its key to the model is the way to
  stop it. A new key is handed to the agent by the page, as its team would,
  and kept in `secrets.env` for its next start.
- The partner's rogue card is the main demo's own showcase of an unchecked A2A
  card (`partner-agent-own`). The Travel Desk switches to it in act 2, and back
  to the card the gateway vetted when it is resumed.
- Each investigation is a one-off monitor in Agent Manager, kept in the
  console under the Travel Desk.
- The agents run in Docker, as externally hosted agents. Agent Manager builds
  and deploys agents itself only from GitHub, so versions here are switched by
  the page, not rolled back from the console.
- Agent Manager 1.0 registers MCP servers only at public addresses, so the
  agents reach Core Banking through the main demo's MCP Gateway, and what they
  may do is also enforced on their model calls (the Cards Agent's rule).
- Agent Manager 1.0's model judges do not work with Claude yet, which is why
  Gemini judges.
