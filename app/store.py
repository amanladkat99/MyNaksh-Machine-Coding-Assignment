"""SQLite persistence for long-term memories."""
from typing import List

from app.db import Database
from app.models import Memory


class MemoryStore:
    def __init__(self, db: Database):
        self.db = db

    def upsert(self, user_id: str, mem: Memory) -> None:
        """Insert, or overwrite the value if (user_id, key) exists - user correction."""
        with self.db.connect() as conn:
            conn.execute(
                """INSERT INTO memories (user_id, key, category, value, confidence)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(user_id, key) DO UPDATE SET
                     value = excluded.value,
                     confidence = excluded.confidence,
                     updated_at = CURRENT_TIMESTAMP""",
                (user_id, mem.key, mem.category, mem.value, mem.confidence),
            )

    def all(self, user_id: str) -> List[Memory]:
        """All memories of a user, highest confidence / most recent first."""
        with self.db.connect() as conn:
            rows = conn.execute(
                "SELECT key, category, value, confidence FROM memories "
                "WHERE user_id = ? ORDER BY confidence DESC, updated_at DESC",
                (user_id,),
            ).fetchall()
        return [Memory(r["key"], r["category"], r["value"], r["confidence"]) for r in rows]
