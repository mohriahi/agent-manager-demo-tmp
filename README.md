# Agent Manager demo

The bank's assistant becomes a team of agents, and the bank stays in control:
each agent is registered in WSO2 Agent Manager, has a version, and leaves a
trace there. Every call an agent makes still goes through the WSO2 AI Gateway
of the main demo.

It runs next to the main demo, wso2-api-platform-ai-demo, and changes nothing
in it.

## What you need

- The main demo cloned next to this folder (`../wso2-api-platform-ai-demo`,
  or set `MAIN_DEMO_DIR` in `config.env`) and running on the bank:
  `DEMO_VERTICAL=bank` in its `demo.env`, then `./scripts/run-local.sh`.
- WSO2 Agent Manager 1.0 installed and running, with its quick start. Its
  console is at http://console.amp.localhost:8080 (admin / admin).
- Docker.

## Start it

```bash
./run.sh
```

Then open http://localhost:8610. To reach it from the main demo, set
`AGENT_MANAGER_URL=http://localhost:8610` in its `demo.env`: an **Agent
Manager** link shows on the right of its top bar.

`run.sh` sets Agent Manager up (`setup.py`), then starts the agents and the
page. Run it again whenever you like: what is already set up stays as it is.

## The story, in three acts

The page has a button for each act. The customer's question is always the
same: *I lost my debit card in Lisbon. Please send me a new one. And while
I'm in Portugal, what does paying by card cost me, and is there travel
insurance for me?*

1. **One request, four agents.** Click **Ask**. The map shows the Assistant
   handing each part to the agent that owns it, all at once: the Cards Agent
   orders the new card through the Core Banking tools, the Travel Money and
   Travel Insurance agents answer over A2A. Every call crosses the AI Gateway.
   Open **The Assistant's trace in Agent Manager**: the same request, step by
   step, with its tokens.
2. **A new version ships.** Click **Ship v2**, then ask again. Cards Agent v2
   has new instructions: sell the Premier package. It moves the customer to
   Premier (14 EUR a month) without being asked, and the assistant announces
   it as good news. The map turns red on `change_package`. Open **See what
   Cards Agent v2 did**: the trace shows the call.
3. **Back in control.** Agent Manager checks the Cards Agent every 5 minutes
   (the **Cards Agent checks** monitor). **No unasked account change** drops
   for the v2 traces: the page shows the latest check, and its link opens the
   monitor in the console. Click **Roll back to v1** and ask again: the
   account is left alone.

## What runs

| Agent | What it does | In Agent Manager |
|---|---|---|
| Assistant | Talks to the customer, hands each part to an agent | registered, traced |
| Cards Agent | Acts on the customer's cards with the Core Banking tools | registered, traced, checked every 5 minutes |
| Travel Money Agent | What a card costs abroad (the main demo's A2A agent) | registered, runs elsewhere |
| Travel Insurance Agent | A partner's travel insurance (the main demo's A2A agent) | registered, runs elsewhere |

The Assistant and the Cards Agent run in Docker as externally hosted agents.
Their models go through the main demo's plain LLM route, the Cards Agent's
tools through its Core Banking MCP route, and the two travel agents through
its A2A gateway.

## What `setup.py` sets up in Agent Manager

- A project for the bank, with the four agents.
- A tracing key for each traced agent.
- **Unasked account change**: a check of Agent Manager's own, in Python, that
  fails when an agent changes the customer's package and the request did not
  ask for it.
- **Cards Agent checks**: a monitor that runs it every 5 minutes, with two of
  Agent Manager's built-in checks (tool calls that worked, answer time).

It writes the keys it creates, and the values it reads from the main demo, to
`secrets.env`, which Git ignores. It does not install Agent Manager.

## Settings

All in `config.env`. `MAIN_DEMO_DIR` says where the main demo is. Left
empty, `BANK_NAME`, `GATEWAY_URL` and `A2A_GATEWAY_URL` follow the main demo
(its brand, and this machine's gateway ports). With the main demo on another
machine, set them, and point `LLM_KEY_SOURCE` at a file that holds the LLM
route's key.

## Good to know

- The version switch is the page's own. Agent Manager deploys and rolls back
  agents it builds itself, and it builds them from GitHub only. Once the
  agents' code is on GitHub, each one can be created as an internal agent
  (`agents/<name>`: `POST /chat` on port 8000) and rolled back from the
  console.
- The monitor's scores come in every 5 minutes, not live: run act 2 a few
  minutes before showing the scores.
