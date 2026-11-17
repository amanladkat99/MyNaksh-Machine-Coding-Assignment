import pytest
from fastapi.testclient import TestClient

from app.db import Database
from app.llm import LLMClient, LLMUnavailable
from app.main import create_app
from app.service import ChatService


class MockLLM(LLMClient):
    """Records every call so tests can inspect what the LLM was given."""

    def __init__(self):
        self.calls = []

    def generate(self, system_prompt, history, user_message):
        self.calls.append({"system": system_prompt, "history": history, "message": user_message})
        return "mock response"


class FailingLLM(LLMClient):
    def generate(self, system_prompt, history, user_message):
        raise LLMUnavailable("down")


@pytest.fixture
def llm():
    return MockLLM()


@pytest.fixture
def make_client(tmp_path):
    def _make(llm):
        service = ChatService(Database(str(tmp_path / "test.db")), llm)
        return TestClient(create_app(service))
    return _make


def send(client, message, user="u1", session="s1"):
    r = client.post("/chat", json={"user_id": user, "session_id": session, "message": message})
    assert r.status_code == 200
    return r.json()


def test_basic_chat_returns_response(make_client, llm):
    data = send(make_client(llm), "Hello there")
    assert data["response"] == "mock response"
    assert data["user_id"] == "u1" and data["session_id"] == "s1"
    assert data["context_used"] == []


def test_memory_saved_and_used_for_followup_question(make_client, llm):
    client = make_client(llm)
    send(client, "I'm planning to switch jobs next year, and I prefer advice in Hindi.")
    data = send(client, "What should I focus on for my career?")
    assert set(data["context_used"]) == {"career_goal", "language_preference"}
    assert "switch jobs" in llm.calls[-1]["system"]
    assert "Respond in Hindi" in llm.calls[-1]["system"]


def test_memory_retrieved_in_new_session(make_client, llm):
    client = make_client(llm)
    send(client, "I'm planning to switch jobs next year.", session="s1")
    data = send(client, "What do you remember about my career plans?", session="s2")
    assert "career_goal" in data["context_used"]
    assert "switch jobs" in llm.calls[-1]["system"]


def test_history_supports_followup(make_client, llm):
    client = make_client(llm)
    send(client, "Will I travel soon?")
    send(client, "Why do you say that?")
    history = llm.calls[-1]["history"]
    assert [h["role"] for h in history] == ["user", "assistant"]
    assert history[0]["content"] == "Will I travel soon?"


def test_history_is_limited_and_session_scoped(make_client, llm):
    client = make_client(llm)
    for i in range(10):
        send(client, f"message {i}")
    assert len(llm.calls[-1]["history"]) == 6
    send(client, "other session", session="s2")
    assert llm.calls[-1]["history"] == []


def test_irrelevant_memories_excluded(make_client, llm):
    client = make_client(llm)
    send(client, "I love painting. I want to switch jobs next year.")
    data = send(client, "What should I focus on for my career?")
    assert "career_goal" in data["context_used"]
    assert not any(k.startswith("interest_") for k in data["context_used"])
    assert "painting" not in llm.calls[-1]["system"]


def test_questions_are_not_stored(make_client, llm):
    client = make_client(llm)
    send(client, "Should I switch jobs next year?")
    assert client.get("/memories/u1").json() == []


def test_memory_correction_updates_existing(make_client, llm):
    client = make_client(llm)
    send(client, "I'm planning to switch jobs next year.")
    send(client, "Actually I want to start a business instead.")
    mems = [m for m in client.get("/memories/u1").json() if m["key"] == "career_goal"]
    assert len(mems) == 1 and "business" in mems[0]["value"]


def test_memories_are_per_user(make_client, llm):
    client = make_client(llm)
    send(client, "I'm planning to switch jobs next year.", user="u1")
    data = send(client, "What do you remember about my career?", user="u2")
    assert data["context_used"] == []


def test_llm_failure_falls_back(make_client):
    client = make_client(FailingLLM())
    send(client, "I want to switch jobs next year.")
    data = send(client, "Tell me about my career")
    assert data["fallback"] is True
    assert "switch jobs" in data["response"]
