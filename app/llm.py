"""LLM integration"""

import os
from abc import ABC, abstractmethod

import httpx


class LLMUnavailable(Exception):
    """Raised when the LLM cannot produce a response (no key, network, API error)."""


class LLMClient(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, history: list[dict], user_message: str) -> str:
        ...


class OpenAICompatibleLLM(LLMClient):
    def __init__(self, api_key=None, base_url=None, model=None, timeout: float = 30.0):
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = (base_url or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.timeout = timeout

    def generate(self, system_prompt: str, history: list[dict], user_message: str) -> str:
        if not self.api_key:
            raise LLMUnavailable("LLM_API_KEY is not set")
        messages = [{"role": "system", "content": system_prompt}, *history,
                    {"role": "user", "content": user_message}]
        try:
            resp = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": messages, "temperature": 0.7},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise LLMUnavailable(str(exc)) from exc
