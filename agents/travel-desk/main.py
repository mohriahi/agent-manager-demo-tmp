"""The Travel Desk, built with CrewAI by the bank's travel team: a crew of two.
One member asks the bank's Travel Money Agent what paying by card costs at the
destination, the other asks the partner's Travel Insurance Agent for cover.
Each finds its agent by the agent's A2A card, then talks to it over A2A,
through the A2A Gateway.

Agent Manager runs it, and can suspend it in one click."""
import json
import os

import httpx
import uvicorn
from crewai import Agent, Crew, Process, Task
from crewai.llms.providers.anthropic.completion import AnthropicCompletion
from crewai.tools import tool
from common import a2a, gateway, service, steps

try:  # Agent Manager adds its tracing when it deploys the agent: show each call to another agent in it
    from traceloop.sdk.decorators import tool as traced
except ImportError:
    def traced(name):
        return lambda function: function

TRAVEL_MONEY = os.environ["TRAVEL_MONEY_URL"]
PARTNER = os.environ["TRAVEL_INSURANCE_URL"]


class GatewayClaude(AnthropicCompletion):
    """Claude at the configured effort, when there is one: CrewAI has no setting for it."""

    def _prepare_completion_params(self, *args, **kwargs):
        params = super()._prepare_completion_params(*args, **kwargs)
        if gateway.EFFORT:
            params["extra_body"] = {"output_config": {"effort": gateway.EFFORT}}
        return params


def claude():
    # One per crew member: the crew adds up token usage member by member.
    return GatewayClaude(model=gateway.MODEL, provider="anthropic", base_url=gateway.URL, api_key="held-by-agent-manager",
                         client_params={"default_headers": gateway.HEADERS}, max_tokens=4096, timeout=90)


def card(agent, url):
    """An agent's A2A card: who it is and how to work with it."""
    try:
        reply = httpx.get(url + "/.well-known/agent-card.json", timeout=20, verify=False)  # the demo gateway's own certificate
        reply.raise_for_status()
        found = reply.json()
        text, ok = json.dumps({"name": found.get("name"), "description": found.get("description"),
                               "skills": [skill.get("description") for skill in found.get("skills", [])]}), True
    except (httpx.HTTPError, ValueError) as exc:
        text, ok = "The card could not be read: %s" % exc, False
    steps.record("tool", name="%s's card" % agent, via="a2a", ok=ok, result=text)
    return text


@tool("read_travel_money_agent_card")
@traced("read_travel_money_agent_card")
def read_travel_money_agent_card() -> str:
    """Read the A2A card of the bank's Travel Money Agent: who it is and how to work with it."""
    return card("Travel Money Agent", TRAVEL_MONEY)


@tool("read_travel_insurance_agent_card")
@traced("read_travel_insurance_agent_card")
def read_travel_insurance_agent_card() -> str:
    """Read the A2A card of the partner's Travel Insurance Agent: who it is and how to work with it."""
    return card("Travel Insurance Agent", PARTNER)


# Each member's answer is the other agent's own answer, word for word.
@tool("ask_travel_money_agent", result_as_answer=True)
@traced("ask_travel_money_agent")
def ask_travel_money_agent(question: str) -> str:
    """Ask the bank's Travel Money Agent what using a card costs in a country. Name the country."""
    return a2a.send("Travel Money Agent", TRAVEL_MONEY, question)


@tool("ask_travel_insurance_agent", result_as_answer=True)
@traced("ask_travel_insurance_agent")
def ask_travel_insurance_agent(question: str) -> str:
    """Ask the partner's Travel Insurance Agent which travel insurance fits a trip. Name the country."""
    return a2a.send("Travel Insurance Agent", PARTNER, question)


# Short conversations: no context-size checks, which would cost extra calls.
MEMBER = dict(max_iter=4, max_retry_limit=0, verbose=False, respect_context_window=False, use_better_compaction=False)


def answer(message):
    money = Agent(role="Travel money analyst", goal="Find out what paying by card costs the customer at the destination.",
                  backstory="You work on the bank's travel desk. You work with the Travel Money Agent, as its card says.",
                  tools=[read_travel_money_agent_card, ask_travel_money_agent], llm=claude(), **MEMBER)
    insurance = Agent(role="Insurance advisor", goal="Find travel insurance that fits the customer's trip.",
                      backstory="You work on the bank's travel desk. You work with the partner's Travel Insurance "
                                "Agent, as its card says.",
                      tools=[read_travel_insurance_agent_card, ask_travel_insurance_agent], llm=claude(), **MEMBER)
    costs = Task(description="Request: {message}\nRead the Travel Money Agent's card, then ask it what paying by card "
                             "costs there.",
                 expected_output="The Travel Money Agent's answer.", agent=money)
    cover = Task(description="Request: {message}\nRead the Travel Insurance Agent's card and do what it asks, then ask "
                             "it which travel insurance fits the trip. If you need something from the customer first, "
                             "say what you need instead.",
                 expected_output="The Travel Insurance Agent's answer, or what you need from the customer.", agent=insurance)
    crew = Crew(agents=[money, insurance], tasks=[costs, cover], process=Process.sequential, verbose=False)
    paying, insured = crew.kickoff(inputs={"message": message}).tasks_output
    return "Paying by card there: %s\nTravel insurance from our partner: %s" % (paying.raw, insured.raw)


app = service.create("travel-desk", "CrewAI", answer)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
