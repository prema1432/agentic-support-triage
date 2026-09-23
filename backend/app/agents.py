"""Multi-agent workflow — a LangGraph-style cyclic run with a human gate.

Flow: TriageAgent -> KnowledgeAgent -> ReviewGate
- TriageAgent classifies via the classify_ticket tool.
- KnowledgeAgent searches the KB and drafts a reply via the draft_reply tool.
- ReviewGate holds the ticket at pending_review (human-in-the-loop) unless the
  classification is low priority, in which case it auto-approves.
"""

from __future__ import annotations

import json
from typing import Any

from app.llm import get_llm
from app.tools import ToolRegistry, default_registry


class AgentRunTrace:
    def __init__(self) -> None:
        self.steps: list[dict[str, Any]] = []

    def add(self, agent: str, action: str, detail: dict[str, Any] | None = None) -> None:
        self.steps.append({"agent": agent, "action": action, "detail": detail or {}})


class TriageAgent:
    name = "triage"

    def __init__(self, llm=None, tools: ToolRegistry | None = None) -> None:
        self.llm = llm or get_llm()
        self.tools = tools or default_registry()

    async def run(self, text: str, trace: AgentRunTrace) -> dict[str, Any]:
        trace.add(self.name, "start", {"text": text[:120]})
        messages = [{"role": "user", "content": text}]
        response = await self.llm.chat(messages, tools=self.tools.specs())
        trace.add(self.name, "llm_call", {"tokens_in": response.tokens_in, "tokens_out": response.tokens_out})

        result: dict[str, Any] = {}
        for call in response.tool_calls:
            tool_result = await self.tools.execute(call["name"], call["arguments"])
            trace.add(self.name, f"tool:{call['name']}", tool_result)
            result = tool_result
        trace.add(self.name, "done", result)
        return result


class KnowledgeAgent:
    name = "knowledge"

    def __init__(self, llm=None, tools: ToolRegistry | None = None) -> None:
        self.llm = llm or get_llm()
        self.tools = tools or default_registry()

    async def run(self, text: str, priority: str, category: str, trace: AgentRunTrace) -> dict[str, Any]:
        trace.add(self.name, "start", {"priority": priority, "category": category})
        kb = await self.tools.execute("search_kb", {"query": text})
        trace.add(self.name, "tool:search_kb", kb)
        draft = await self.tools.execute(
            "draft_reply", {"text": text, "priority": priority, "category": category}
        )
        trace.add(self.name, "tool:draft_reply", draft)
        out = {"kb": kb, "draft": draft.get("draft", "")}
        trace.add(self.name, "done", out)
        return out


class ReviewGate:
    """Human-in-the-loop gate — auto-approves only low-priority tickets."""

    AUTO_APPROVE_PRIORITIES = {"low"}

    @staticmethod
    def decide(priority: str) -> tuple[str, bool]:
        needs_human = priority not in ReviewGate.AUTO_APPROVE_PRIORITIES
        status = "pending_review" if needs_human else "approved"
        return status, needs_human


async def run_workflow(text: str, tools: ToolRegistry | None = None) -> dict[str, Any]:
    trace = AgentRunTrace()
    triage = TriageAgent(llm=get_llm(), tools=tools or default_registry())
    classification = await triage.run(text, trace)

    priority = classification.get("priority", "low")
    category = classification.get("category", "general")

    knowledge = KnowledgeAgent(llm=get_llm(), tools=tools or default_registry())
    knowledge_out = await knowledge.run(text, priority, category, trace)

    status, needs_human = ReviewGate.decide(priority)
    trace.add("review_gate", "decision", {"status": status, "needs_human": needs_human})

    return {
        "priority": priority,
        "category": category,
        "draft": knowledge_out["draft"],
        "kb": knowledge_out["kb"],
        "status": status,
        "needs_human": needs_human,
        "steps": trace.steps,
    }
