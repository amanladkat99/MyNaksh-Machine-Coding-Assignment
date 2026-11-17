import pytest

from app.db import Database
from app.extractor import MemoryExtractor
from app.models import Memory
from app.retriever import MemoryRetriever
from app.store import MemoryStore


def keys(memories):
    return {m.key for m in memories}


# ----------------------------------------------------------- extractor
def test_extracts_goal_and_language_from_one_message():
    mems = MemoryExtractor().extract("I'm planning to switch jobs next year, and I prefer advice in Hindi.")
    assert keys(mems) == {"career_goal", "language_preference"}
    assert next(m for m in mems if m.key == "language_preference").value == "Hindi"


@pytest.mark.parametrize("text", [
    "What should I focus on for my career?",   # question
    "Hello, how are you",                      # small talk
    "I don't want to switch jobs",             # negated goal
])
def test_nothing_extracted(text):
    assert MemoryExtractor().extract(text) == []


def test_extracts_interest_and_personal_facts():
    mems = MemoryExtractor().extract("My name is aman. I love painting.")
    by_key = {m.key: m for m in mems}
    assert by_key["name"].value == "Aman"
    assert by_key["interest_painting"].category == "interest"


# ----------------------------------------------------------- retriever
@pytest.fixture
def retriever(tmp_path):
    store = MemoryStore(Database(str(tmp_path / "t.db")))
    store.upsert("u", Memory("career_goal", "career", "switch jobs next year", 0.85))
    store.upsert("u", Memory("language_preference", "preference", "Hindi", 0.95))
    store.upsert("u", Memory("interest_painting", "interest", "painting", 0.7))
    return MemoryRetriever(store, max_results=5)


def test_career_question_returns_career_and_language_only(retriever):
    result = retriever.retrieve("u", "What should I focus on for my career?")
    assert keys(result) == {"career_goal", "language_preference"}


def test_recall_without_topic_returns_everything(retriever):
    assert len(retriever.retrieve("u", "What do you remember about me?")) == 3


def test_recall_with_topic_is_filtered(retriever):
    result = retriever.retrieve("u", "What do you remember about my career plans?")
    assert "career_goal" in keys(result) and "interest_painting" not in keys(result)


def test_max_results_is_respected(retriever):
    retriever.max_results = 1
    assert len(retriever.retrieve("u", "What do you remember about me?")) == 2  # recall allows 2x
    assert len(retriever.retrieve("u", "career advice please")) == 1
