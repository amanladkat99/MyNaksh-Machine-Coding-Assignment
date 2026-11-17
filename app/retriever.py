"""Picks only the relevant memories."""
import re
from typing import List

from app.models import Memory
from app.store import MemoryStore
from app.topics import RECALL_PATTERN, STOPWORDS, detect_topics


class MemoryRetriever:
    def __init__(self, store: MemoryStore, max_results: int = 5):
        self.store = store
        self.max_results = max_results

    def retrieve(self, user_id: str, question: str) -> List[Memory]:
        memories = self.store.all(user_id)  # already sorted by confidence
        topics = detect_topics(question)
        recall = bool(RECALL_PATTERN.search(question))

        # "What do you remember about me?" with no topic -> everything we have
        if recall and not topics:
            return memories[: self.max_results * 2]

        question_tokens = {
            t for t in re.findall(r"[a-z]+", question.lower())
            if len(t) > 3 and t not in STOPWORDS
        }
        selected: List[Memory] = []
        for mem in memories:
            if mem.category == "preference":
                selected.append(mem)  # language etc. shapes every answer
            elif mem.category in topics:
                selected.append(mem)  # topic match: career question -> career goal
            elif question_tokens & set(re.findall(r"[a-z]+", mem.value.lower())):
                selected.append(mem)  # direct keyword overlap with the memory text
        return selected[: self.max_results]
