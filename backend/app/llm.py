"""LLM provider abstraction — mock by default, OpenAI-compatible when configured.

The mock provider is deterministic so the demo runs with zero API keys.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolSpec:
    """A callable tool the agent may invoke."""

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    content: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0


class BaseLLMProvider:
    """Interface for chat completion providers with tool binding."""

    name = "base"

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[ToolSpec] | None = None,
    ) -> LLMResponse:
        raise NotImplementedError


class MockLLMProvider(BaseLLMProvider):
    """Deterministic rule-based provider used for demos, tests and CI."""

    name = "mock"

    URGENT = re.compile(r"\b(outage|down|cannot log in|breach|security|refund now)\b", re.I)
    HIGH = re.compile(r"\b(error|failed|broken|bug|crash|timeout)\b", re.I)
    BILLING = re.compile(r"\b(invoice|billing|charge|refund|payment)\b", re.I)
    TECHNICAL = re.compile(r"\b(api|sdk|integration|webhook|auth|error|bug|crash)\b", re.I)

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[ToolSpec] | None = None,
    ) -> LLMResponse:
        user_text = next((m["content"] for m in messages if m["role"] == "user"), "")
        last = messages[-1] if messages else {"role": "user", "content": ""}

        if last["role"] == "tool":
            # Finalize after tool results come back.
            return LLMResponse(
                content=f"Based on tool results ({last['content'][:80]}...), the draft reply is ready for review.",
                tokens_in=42,
                tokens_out=58,
            )

        wants_tool = any(t.name == "classify_ticket" for t in (tools or []))
        if wants_tool:
            return LLMResponse(
                content="Calling the classification tool.",
                tool_calls=[
                    {
                        "id": "call_1",
                        "name": "classify_ticket",
                        "arguments": {"text": user_text},
                    }
                ],
                tokens_in=31,
                tokens_out=17,
            )

        return LLMResponse(content="How can I help with your support request?", tokens_in=12, tokens_out=9)


class LLMProviderFactory:
    _providers: dict[str, type[BaseLLMProvider]] = {"mock": MockLLMProvider}

    @classmethod
    def register(cls, name: str, provider: type[BaseLLMProvider]) -> None:
        cls._providers[name] = provider

    @classmethod
    def create(cls, name: str) -> BaseLLMProvider:
        try:
            return cls._providers[name]()
        except KeyError:
            raise ValueError(f"Unknown LLM provider: {name}") from None


def get_llm() -> BaseLLMProvider:
    from app.settings import settings

    return LLMProviderFactory.create(settings.llm_provider)
