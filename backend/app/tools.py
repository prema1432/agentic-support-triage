"""Tool registry — the functions agents may call during a run."""

from __future__ import annotations

import json
from typing import Any, Awaitable, Callable

from app.llm import ToolSpec

ToolFunc = Callable[..., Awaitable[dict[str, Any]]]


class ToolRegistry:
    def __init__(self) -> None:
        self._specs: dict[str, ToolSpec] = {}
        self._funcs: dict[str, ToolFunc] = {}

    def register(self, spec: ToolSpec, func: ToolFunc) -> None:
        self._specs[spec.name] = spec
        self._funcs[spec.name] = func

    def specs(self) -> list[ToolSpec]:
        return list(self._specs.values())

    async def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in self._funcs:
            return {"error": f"unknown tool {name}"}
        try:
            return await self._funcs[name](**arguments)
        except TypeError as exc:
            return {"error": f"bad arguments for {name}: {exc}"}


def default_registry() -> ToolRegistry:
    registry = ToolRegistry()

    async def classify_ticket(text: str) -> dict[str, Any]:
        from app.llm import MockLLMProvider

        if MockLLMProvider.URGENT.search(text):
            priority, category = "urgent", "incident"
        elif MockLLMProvider.HIGH.search(text):
            priority, category = "high", "bug"
        elif MockLLMProvider.BILLING.search(text):
            priority, category = "medium", "billing"
        else:
            priority, category = "low", "general"
        return {"priority": priority, "category": category}

    async def search_kb(query: str) -> dict[str, Any]:
        kb = {
            "api": "Rate limits reset hourly. Use exponential backoff on 429 responses.",
            "auth": "Password resets require the email verified flag. Check the auth FAQ.",
            "billing": "Invoices are generated on the 1st. Refunds take 5-7 business days.",
            "webhook": "Webhook retries use jittered backoff for 24 hours.",
        }
        for key, answer in kb.items():
            if key in query.lower():
                return {"source": f"kb:{key}", "answer": answer}
        return {"source": "kb:none", "answer": "No matching knowledge base article."}

    async def draft_reply(text: str, priority: str, category: str) -> dict[str, Any]:
        templates = {
            "incident": "We are aware of the outage and our on-call team is engaged. Updates every 15 minutes.",
            "bug": "Thanks for the report — engineering has been notified and we will follow up shortly.",
            "billing": "Our billing team will review the charge and respond within one business day.",
            "general": "Thanks for reaching out! A specialist will get back to you soon.",
        }
        body = templates.get(category, templates["general"])
        return {"draft": f"[{priority}/{category}] {body}"}

    registry.register(
        ToolSpec(
            name="classify_ticket",
            description="Classify a support ticket into priority and category",
            parameters={"text": "str"},
            ),
        classify_ticket,
    )
    registry.register(
        ToolSpec(
            name="search_kb",
            description="Search the internal knowledge base",
            parameters={"query": "str"},
        ),
        search_kb,
    )
    registry.register(
        ToolSpec(
            name="draft_reply",
            description="Draft a customer reply from classification and KB context",
            parameters={"text": "str", "priority": "str", "category": "str"},
        ),
        draft_reply,
    )
    return registry
