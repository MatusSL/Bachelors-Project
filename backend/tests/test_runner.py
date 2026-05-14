from __future__ import annotations

import pytest
from httpx import HTTPError
from langchain.messages import AIMessage, HumanMessage
from langchain_core.exceptions import LangChainException

from backend.agents.runner import Runner
from backend.schemas.exceptions import AgentExecutionError


class Agent:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def invoke(self, payload):
        self.calls += 1
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_extract_content_returns_last_ai_message_string_content():
    runner = Runner()

    assert runner._extract_content({"messages": [HumanMessage("hello"), AIMessage("answer")]}) == "answer"


def test_extract_content_joins_list_content_items():
    runner = Runner()

    assert runner._extract_content({"messages": [AIMessage(content=["a", {"b": 1}])]} ) == "a {'b': 1}"


@pytest.mark.parametrize("response", [{}, {"messages": []}, {"messages": [HumanMessage("not ai")]}])
def test_extract_content_rejects_malformed_or_human_last_messages(response):
    runner = Runner()

    with pytest.raises(ValueError):
        runner._extract_content(response)


def test_invoke_agent_passes_human_message_payload_and_returns_content():
    runner = Runner()
    agent = Agent([{"messages": [AIMessage("ok")]}])

    assert runner.invoke_agent(agent, "hello") == "ok"
    assert agent.calls == 1


def test_invoke_agent_retries_http_errors_then_succeeds(monkeypatch):
    sleeps: list[int] = []
    monkeypatch.setattr("backend.agents.runner.time.sleep", sleeps.append)
    runner = Runner()
    agent = Agent([HTTPError("temporary"), HTTPError("temporary"), {"messages": [AIMessage("ok")]}])

    assert runner.invoke_agent(agent, "hello") == "ok"
    assert agent.calls == 3
    assert sleeps == [1, 2]


def test_invoke_agent_raises_after_all_retryable_http_errors(monkeypatch):
    monkeypatch.setattr("backend.agents.runner.time.sleep", lambda _: None)
    runner = Runner()
    agent = Agent([HTTPError("temporary"), HTTPError("temporary"), HTTPError("temporary")])

    with pytest.raises(AgentExecutionError):
        runner.invoke_agent(agent, "hello")
    assert agent.calls == 3


def test_invoke_agent_wraps_invalid_response_as_agent_execution_error():
    runner = Runner()
    agent = Agent([{"messages": []}])

    with pytest.raises(AgentExecutionError):
        runner.invoke_agent(agent, "hello")


def test_invoke_agent_does_not_retry_langchain_errors():
    runner = Runner()
    agent = Agent([LangChainException("bad chain")])

    with pytest.raises(AgentExecutionError):
        runner.invoke_agent(agent, "hello")
    assert agent.calls == 1
