"""Finding facts in a message"""

import re
from typing import List
from app.models import Memory
from app.topics import GOAL_TOPICS, GOAL_WORDS, LANGUAGES, NEGATION


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40]


class MemoryExtractor:
    """Turns a user message into a list of Memory objects - possibly empty."""

    def extract(self, message: str) -> List[Memory]:
        memories: List[Memory] = []
        for clause in self._clauses(message):
            memories.extend(self._from_clause(clause))
        return memories

    @staticmethod
    def _clauses(message: str) -> List[str]:
        """Split message into sentences, drop questions, then split on ', and' / 'but' / ','."""
        sentences = re.findall(r"[^.!?;\n]+[.!?]?", message)
        clauses: List[str] = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or sentence.endswith("?"):
                continue  # a question is not a fact about the user
            parts = re.split(r",\s*and\s+|\s+but\s+|,\s+", sentence)
            clauses.extend(p.strip(" ,.") for p in parts if p.strip(" ,."))
        return clauses

    def _from_clause(self, clause: str) -> List[Memory]:
        found: List[Memory] = []

        # Language preference -> 'language_preference'
        m = re.search(
            rf"\b(prefer\w*|speak|reply|respond|answer|talk|advice|write|comfortable)\b"
            rf".*?\bin\s+({LANGUAGES})\b",
            clause, re.I,
        )
        if m:
            found.append(Memory("language_preference", "preference", m.group(2).capitalize(), 0.95))

        negated = bool(NEGATION.search(clause))

        # Goals / plans -> '<topic>_goal' (skipped when negated: "I don't want to ...")
        if not negated and re.search(GOAL_WORDS, clause, re.I):
            for topic, keywords in GOAL_TOPICS.items():
                if re.search(rf"\b({keywords})\b", clause, re.I):
                    found.append(Memory(f"{topic}_goal", topic, clause, 0.85))

        # Interests -> 'interest_<slug>'
        m = re.search(
            r"\b(?:i|i'm|i am)\s+(?:(?:really|also)\s+)?(?:like|love|enjoy|interested in|passionate about|into)\s+(.+)",
            clause, re.I,
        )
        if m and not negated:
            thing = m.group(1).strip()
            found.append(Memory(f"interest_{_slug(thing)}", "interest", thing, 0.7))

        # Personal facts
        m = re.search(r"\b(?:my name is|call me)\s+([A-Za-z]+)", clause, re.I)
        if m:
            found.append(Memory("name", "personal", m.group(1).capitalize(), 0.95))
        m = re.search(r"\bi\s*(?:was|am)\s+born\s+(?:on|in|at)\s+(.+)", clause, re.I)
        if m:
            found.append(Memory("birth_info", "personal", m.group(1).strip(), 0.9))
        m = re.search(r"\bi work as\s+(?:an?\s+)?(.+)", clause, re.I)
        if m:
            found.append(Memory("occupation", "personal", m.group(1).strip(), 0.85))
        return found
