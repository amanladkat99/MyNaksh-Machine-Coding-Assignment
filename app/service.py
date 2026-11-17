"""Chat orchestration"""
import logging
from typing import List

from app.config import Settings
from app.db import Database
from app.extractor import MemoryExtractor
from app.history import HistoryStore
from app.llm import LLMClient, LLMUnavailable
from app.models import Memory
from app.retriever import MemoryRetriever
from app.store import MemoryStore

logger = logging.getLogger(__name__)

SYSTEM_TEMPLATE = (
    "You are a warm, helpful astrology advisor. Give personalized guidance based on "
    "the user's context below. Do not invent personal facts that are not listed.\n"
    "{language_rule}\n"
    "Relevant things you know about the user:\n{memories}"
)


class ChatService:
    def __init__(self, db: Database, llm: LLMClient, settings: Settings = Settings()):
        self.llm = llm
        self.history = HistoryStore(db, max_messages=settings.history_size)
        self.store = MemoryStore(db)
        self.extractor = MemoryExtractor()
        self.retriever = MemoryRetriever(self.store, max_results=settings.max_memories)

    def chat(self, user_id: str, session_id: str, message: str) -> dict:
        # 1. Save any new long-term info first, so it can be used in this very reply
        for mem in self.extractor.extract(message):
            self.store.upsert(user_id, mem)

        # 2. Pick only memories relevant to this question (not everything)
        relevant = self.retriever.retrieve(user_id, message)

        # 3. Recent history of this session (does not include the current message)
        history = self.history.recent(session_id)

        # 4. Generate the answer; degrade gracefully if the LLM is unavailable
        fallback = False
        try:
            response = self.llm.generate(self._system_prompt(relevant), history, message)
        except LLMUnavailable as exc:
            logger.warning("LLM unavailable, using fallback: %s", exc)
            fallback = True
            response = self._fallback(relevant)

        # 5. Persist this turn for future follow-ups
        self.history.add(session_id, "user", message)
        self.history.add(session_id, "assistant", response)

        return {
            "user_id": user_id,
            "session_id": session_id,
            "response": response,
            "context_used": [m.key for m in relevant],
            "fallback": fallback,
        }

    @staticmethod
    def _system_prompt(memories: List[Memory]) -> str:
        lang = next((m.value for m in memories if m.key == "language_preference"), None)
        language_rule = f"Respond in {lang}." if lang else "Respond in the user's language."
        lines = "\n".join(f"- {m.key}: {m.value}" for m in memories) or "- (nothing relevant)"
        return SYSTEM_TEMPLATE.format(language_rule=language_rule, memories=lines)

    @staticmethod
    def _fallback(memories: List[Memory]) -> str:
        if not memories:
            return "I'm having trouble reaching my advisor right now. Please try again shortly."
        facts = "; ".join(f"{m.key}: {m.value}" for m in memories)
        return f"I'm having trouble reaching my advisor right now, but I remember this about you: {facts}."
