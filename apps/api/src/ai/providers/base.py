from __future__ import annotations

import abc
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AIResponse:
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    raw_response: dict[str, Any] = field(default_factory=dict)


class AIProvider(abc.ABC):
    """Abstract base for AI providers (Groq, Anthropic, etc.)."""

    provider_name: str = "base"
    default_model: str = ""

    @abc.abstractmethod
    async def generate(
        self,
        *,
        system_prompt: str | None = None,
        user_prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> AIResponse:
        ...

    async def generate_with_timing(
        self,
        **kwargs: Any,
    ) -> AIResponse:
        start = time.monotonic()
        response = await self.generate(**kwargs)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        response.latency_ms = elapsed_ms
        return response
