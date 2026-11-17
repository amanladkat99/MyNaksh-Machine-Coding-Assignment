"""FastAPI layer - entrypoint"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.config import Settings
from app.db import Database
from app.llm import OpenAICompatibleLLM
from app.service import ChatService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    session_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    user_id: str
    session_id: str
    response: str
    context_used: List[str]
    fallback: bool = False


def create_app(service: Optional[ChatService] = None) -> FastAPI:
    """App factory. Tests inject a ChatService with a mock LLM and a temp DB.

    The real service (and SQLite file) is created lazily on first use, so
    importing this module has no side effects.
    """
    app = FastAPI(title="Personalized AI Chat")
    holder = {"service": service}

    def get_service() -> ChatService:
        if holder["service"] is None:
            settings = Settings.from_env()
            llm = OpenAICompatibleLLM(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                model=settings.llm_model,
                timeout=settings.llm_timeout,
            )
            holder["service"] = ChatService(Database(settings.db_path), llm, settings)
        return holder["service"]

    @app.post("/chat", response_model=ChatResponse)
    def chat(req: ChatRequest):
        return get_service().chat(req.user_id, req.session_id, req.message)

    @app.get("/memories/{user_id}")
    def memories(user_id: str):
        """Debug helper: list everything stored for a user."""
        return [m.__dict__ for m in get_service().store.all(user_id)]

    return app


app = create_app()
