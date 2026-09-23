"""Pydantic schemas for tickets and approvals."""

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

TicketStatus = Literal["pending_review", "approved", "rejected", "resolved"]

Priority = Literal["low", "medium", "high", "urgent"]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    body: str = Field(min_length=10)
    customer_tier: Literal["free", "pro", "enterprise"] = "free"


class TicketOut(BaseModel):
    id: str
    subject: str
    body: str
    customer_tier: str
    status: TicketStatus
    priority: Priority | None = None
    category: str | None = None
    draft_reply: str | None = None
    reviewer: str | None = None
    review_note: str | None = None
    agent_trace: list[dict[str, Any]] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ApprovalIn(BaseModel):
    decision: Literal["approved", "rejected"]
    reviewer: str = Field(min_length=2, max_length=80)
    note: str | None = None


class RunIn(BaseModel):
    ticket_id: str


class RunOut(BaseModel):
    ticket_id: str
    status: TicketStatus
    steps: list[dict[str, Any]]
    needs_human: bool
