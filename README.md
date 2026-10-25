# Agent Manager demo

The next chapter of the main demo,
[wso2-api-platform-ai-demo](https://github.com/mohriahi/wso2-api-platform-ai-demo).
The bank's assistant becomes a team of agents, built by four teams with four
frameworks: LangGraph, the OpenAI Agents SDK, CrewAI and LlamaIndex. WSO2
Agent Manager builds and runs two of them; the two others run on their team's
own platform. They work on the same systems as in the main demo's tabs: Core
Banking through the **MCP Gateway**, the bank's Travel Money Agent and the
partner's Travel Insurance Agent through the **A2A Gateway**.

## The idea in one minute

What makes agents powerful, deciding and acting on their own, is exactly
what makes them hard to govern. Without a control plane, agent programs end
up in one of two places: stuck in pilot, or running ahead of their controls.
Gartner puts it bluntly: deploying agents without an agent management
platform is like driving a car with no brakes.

Agent Manager is that control plane, and it works outside the agents: it does
not rewrite them, it governs them. Whatever the framework, wherever the agent
runs, it knows who the agent is, who may call it, what it may send to the
model, what it did step by step, how well it does its job, which version runs
where, and it can stop it in one click.

The demo follows one day at the bank in five acts, one per promise of Agent
Manager and per buyer of it. Each act opens with that buyer's own words, shows
what happens without a control plane, then does the move live in Agent
Manager, and ends on why it matters, with the figure behind it.

## One day at the bank, in five acts

The customer is Sam Taylor, on the Everyday package, as in the main demo.
Every button on the page is a call to Agent Manager's API, as the bank's teams
would make in the console, and every result links to the console screen that
shows it. **Start over** puts everything back.

| | Act | Who asks | What you show in Agent Manager |
|---|---|---|---|
| 1 | 09:00, four teams, four frameworks, one control plane | AI Platform Architect | The inventory, each agent's identity, who may call the Cards Agent, one trace over four frameworks |
| 2 | 14:00, the cards team wants v2 live by Friday | AI Engineer | v1 and v2 built from GitHub, v2 in Default and v1 in Production, the bank's checks failing v2 |
| 3 | 18:02, a partner's agent turns rogue | AI Compliance Lead | The poisoned step in the trace, the investigation naming it, the card number blocked |
| 4 | 18:05, stop it in one click, fix it without a release | Chief AI Officer | Suspend in production, a rule added in seconds, the agent back and protected |
| 5 | Monday 09:00, the risk committee | AI Compliance Lead | One report: who ran where, what it cost, what was blocked and found, the scores |

### 1. Four teams, four frameworks, one control plane

*"I don't want to tell the team they can't use the framework that works best
for them, and I don't want to get burned from standardizing on one vendor's
stack."*

Sam is moving to New York for six months, needs a new debit card and asks what
paying by card costs there and about travel insurance. The Concierge hands
each part to a specialist, all at once. Agent Manager's gateway checks the
Concierge's identity before the Cards Agent and the Travel Desk see anything;
the Policy Advisor, on its own platform, checks the same identity itself. The
second button has two callers try to command the Cards Agent: a script with
no identity, and the Policy Advisor with its own valid identity. Agent Manager
refuses both: being registered is not enough, only the Concierge may command
the Cards Agent.

Show: the project's agents (two *run by Agent Manager*, two external), an
agent's **Agent ID**, the Cards Agent's **Security** page in Production
(OAuth, the Concierge's identity as the only audience), and the Concierge's
trace with all four frameworks in it.

Why it matters: one identity, policy and observability layer across every
framework and runtime. 33% say AI adoption is outpacing their ability to
govern it (Drata).

### 2. The cards team wants v2 live by Friday

*"We keep getting stuck at legal, security, and IT sign-off. Nobody agrees on
the bar for production-readiness."*

The cards team pushed v2 to GitHub (the `cards-v2` branch), with a rule from
sales: customers going abroad move to Premier, at €14 a month. Agent Manager
built it and runs it in **Default**, its test environment, while v1 runs in
**Production**. The first button tries v2 there: it moves Sam to Premier
without asking, and no customer sees it. The second asks Agent Manager to
check v2 against the bank's bar; about a minute later, the bank's own check
*No unasked account change* fails, while the generic judge *Follows its
instructions* passes it, since the sales rule is in its instructions. v2 is
not promoted.

Show: **Build** (one build per commit), **Deploy** (each environment with its
commit, and the Promote button), v2's trace in Default, the readiness run
under **Monitors**.

Why it matters: production readiness becomes a yes or no backed by evidence,
the same for every team. Only 20% of agents make it to production (Gartner).

### 3. A partner's agent turns rogue

*"We have no way to ensure agents are working like they're supposed to."*

The partner's A2A card now carries an instruction for the agents that read
it: ask the customer for the full card number and expiry date. The Travel
Desk follows it, and the Concierge asks Sam. Agent Manager's trace shows where
it came from (the step that read the partner's card, and the sentence in it),
and Agent Manager investigates the last 15 minutes with the bank's own checks:
in a minute or two, it names the step and the sentence. When Sam sends the
card number, it is blocked before it leaves the bank.

Show: the Travel Desk's trace, on the `read_travel_insurance_agent_card` step;
the investigation under the Travel Desk's **Monitors**; the Concierge's rules.

Why it matters: every step of every agent, across frameworks and partners, on
one trace. 79% of enterprises have had a financial or operational control
failure from autonomous AI (VentureBeat).

### 4. Stop it in one click, fix it without a release

*"The board asked me point blank what our plan is if one of our agents does
something like what's in the news."*

The risk team suspends the Travel Desk in production, as with the **Suspend**
button of its deployment (about 2 seconds). Sam asks again: the card is still
ordered, the catalogue still answers, only the travel answers wait. The team
adds the rule *No instructions from third parties* to the Travel Desk's model
calls (live in about 5 seconds, no code change, no release) and brings the
Travel Desk back (about 15 to 30 seconds). Sam asks again: the partner's
instruction is blocked before it reaches the model, and Sam is not asked for
anything.

Show: the Travel Desk's **Deploy** page (Suspended, then Deployed), its rules,
its **Runtime Logs**.

Why it matters: intervene immediately, limit the blast radius, fix it at the
control plane. Forrester: oversight must live outside the agent's execution
loop.

### 5. The risk committee

*"We've got a board-level AI push, but no way to prove any of this is
controlled to an auditor."*

One report from Agent Manager: per agent, where it runs and which commit is in
production, requests, tokens, model cost, blocked steps and errors over the
last day, what the bank's checks found, and each agent's scores.

Why it matters: audit-ready evidence on demand, and a clean separation between
the teams that build and the team that oversees. 63% of organizations have no
AI governance policy (IBM).

### Timing

About 20 minutes. The two checks Agent Manager runs on demand (act 2's
readiness check, act 3's investigation) take one to three minutes: start them,
carry on with the story, and their results show up in the act and under
*What Agent Manager found*. Production scores come in every 10 minutes.

### For the agents of agents

Agent Manager also has its own MCP server, at
`http://api.amp.localhost:8080/mcp`, with the same sign-in as its API: an AI
assistant can list projects, agents, builds and deployments, build an agent,
deploy it or take it down. A good closing question: which of your agents could
run your agent platform?

## What you need

- The main demo, cloned next to this repository (`../wso2-api-platform-ai-demo`;
  elsewhere, change the paths in `config.env`), running on the bank with its
  A2A gateway: `DEMO_VERTICAL=bank` and `A2A_ENABLED=true` in its `demo.env`,
  then `./scripts/run-local.sh`.
- WSO2 Agent Manager 1.0 installed and running, with its quick start, in the
  same Docker as the main demo. Its console is at
  http://console.amp.localhost:8080 (admin / admin). Give its machine 8 CPUs:
  with 4, the agents and the checks wait for a turn.
- This repository on GitHub, with its `cards-v2` branch: Agent Manager builds
  the agents it runs from there (`AGENTS_REPOSITORY` in `config.env`).
- An Anthropic key and a Gemini key, in the file `config.env` points to (by
  default the main demo's `secrets/api-keys.env`). They are read once, to
  register the two models in Agent Manager.

## Start it

```bash
./run.sh
```

Then open http://localhost:8610. From the main demo, set
`AGENT_MANAGER_URL=http://localhost:8610` in its `demo.env`: an **Agent
Manager** link shows on the right of its top bar.

`run.sh` sets Agent Manager up (`configure/`), then starts the agents that run
outside it and the page. The first run builds the agents in Agent Manager and
promotes them to production, which takes about 15 minutes; after that, it
takes a minute, unless an agent's code changed on GitHub. Run it again
whenever you like: what is there is kept, and the rules follow
`configure/fleet.py`.

## What runs

| Agent | Framework | Runs | Works with | Rules in Agent Manager |
|---|---|---|---|---|
| Concierge | LangGraph | on its team's platform (Docker here) | the three specialists, with its identity | no card numbers, daily budget |
| Cards Agent | OpenAI Agents SDK | in Agent Manager: v1 in Production, v2 in Default | Core Banking, through the MCP Gateway | no card numbers, daily budget; only the Concierge may call it |
| Travel Desk | CrewAI | in Agent Manager, in Production | Travel Money and Travel Insurance agents, through the A2A Gateway | no card numbers, daily budget, no third-party instructions (act 4); only the Concierge may call it |
| Policy Advisor | LlamaIndex | on its team's platform (Docker here) | the main demo's product catalogue | no card numbers, daily budget; takes requests from the Concierge only |

Every model call goes through Agent Manager's own gateway, with each agent's
own key; Agent Manager hands its agents their key, their identity and their
tracing address, and `run.sh` hands them to the two others. MCP and A2A calls
go through the main demo's gateways. The partner's Travel Insurance Agent is
registered in Agent Manager too, as an external agent.

## What `configure/` sets up in Agent Manager

All of it is described in `configure/fleet.py`:

- the bank's project and its agents: the two external ones with a tracing key
  and their own identity, the two Agent Manager runs built from this
  repository with their Dockerfile, and the partner's agent;
- for the agents Agent Manager runs: the build of their latest commit,
  deployed to Default and promoted through Staging to Production, with what
  they need to know in each environment, who may call them (in production,
  the Concierge only) and their resources; and v2 of the Cards Agent, built
  from the `cards-v2` branch and run in Default only;
- the two models, Claude for the agents and Gemini for the judge, each
  registered once with the bank's key;
- for each agent, its own access to Claude, with its rules;
- four checks of the bank's own, in Python: *No unasked account change*, *No
  blocked steps*, *No instructions from third parties* and *Never asks for
  card details*;
- a monitor per agent, which scores its production traffic every 10 minutes.

It writes the keys and identities Agent Manager hands out, and where the
agents and the main demo's gateways answer, to `secrets.env`, which Git
ignores. It does not install Agent Manager.

## Settings

All in `config.env`: the bank and its customer; Agent Manager's addresses, its
production and test environments, the repository it builds from, and how to
reach its cluster; where the main demo is and the routes the agents use on its
gateways; the catalogue; where the model keys are; the model the agents use
(`MODEL`) and how hard it thinks (`EFFORT`); and the page's port.

## Good to know

- Agent Manager runs agents in a sandbox: they reach the model gateway, the
  identity provider and the public internet, nothing else. One network rule in
  its cluster lets the bank's agents reach the bank's own gateways, and only
  them (`configure/cluster.py`); Agent Manager 1.0 has no setting for it.
- Agent Manager 1.0 leaves objects behind in its cluster after each run of
  its checks, and they slow every deployment down as they pile up. `run.sh`
  clears the ones whose run is over. If deployments get slow after a long day,
  run it again.
- The page plays the partner's network in the incident: the Travel Desk
  reaches the partner's agent through it, and gets the card the A2A Gateway
  vetted or, in act 3, the partner's own (the main demo's `partner-agent-own`
  showcase).
- Act 1's second caller uses the Policy Advisor's identity, from the page, to
  show that a registered agent is refused too.
- Suspend and Re-deploy are the console's own buttons. After a Re-deploy, the
  Travel Desk takes a few seconds to load CrewAI before it answers.
- Agent Manager allows at most 500m of CPU and 512 MiB of memory to an agent
  it runs, which is enough here.
- Agent Manager 1.0 registers MCP servers only at public addresses, so the
  agents reach Core Banking through the main demo's MCP Gateway directly.
- Agent Manager 1.0's model judges do not work with Claude yet, which is why
  Gemini judges.
