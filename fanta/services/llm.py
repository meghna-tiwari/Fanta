from __future__ import annotations

import time
from typing import Protocol

from fanta.config import AppConfig

try:
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None


class LLMClient(Protocol):
    def ask(self, system_prompt: str, user_prompt: str, retries: int = 3) -> str:
        ...


class GroqLLMClient:
    def __init__(self, config: AppConfig):
        self.config = config
        self.client = None
        if Groq and config.groq_api_key:
            self.client = Groq(api_key=config.groq_api_key)

    def ask(self, system_prompt: str, user_prompt: str, retries: int = 3) -> str:
        if not self.client:
            raise RuntimeError("Groq client is not configured. Set GROQ_API_KEY to enable LLM orchestration.")

        last_error: Exception | None = None
        for _ in range(retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.config.groq_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=1200,
                )
                return response.choices[0].message.content or "{}"
            except Exception as exc:  # pragma: no cover
                last_error = exc
                time.sleep(2)

        raise RuntimeError(f"Groq request failed after {retries} attempts: {last_error}")
