"""Configuration"""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_timeout: float = 30.0
    db_path: str = "chat.db"
    history_size: int = 6      # recent messages sent to the LLM
    max_memories: int = 5      # max memories placed in the prompt

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_base_url=os.getenv("LLM_BASE_URL", cls.llm_base_url).rstrip("/"),
            llm_model=os.getenv("LLM_MODEL", cls.llm_model),
            db_path=os.getenv("DB_PATH", cls.db_path),
        )
