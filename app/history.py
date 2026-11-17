"""Short-term, per-session conversation history."""
from app.db import Database


class HistoryStore:
    def __init__(self, db: Database, max_messages: int = 6):
        self.db = db
        self.max_messages = max_messages

    def add(self, session_id: str, role: str, content: str) -> None:
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content),
            )

    def recent(self, session_id: str) -> list[dict]:
        """Last N messages of the session, oldest first."""
        with self.db.connect() as conn:
            rows = conn.execute(
                "SELECT role, content FROM messages WHERE session_id = ? "
                "ORDER BY id DESC LIMIT ?",
                (session_id, self.max_messages),
            ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
