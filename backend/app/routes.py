"""REST endpoints for the support triage API."""

from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_db
from app.agents import run_workflow
from app.schemas import ApprovalIn, RunIn, RunOut, TicketCreate, TicketOut, TicketStatus, utcnow

router = APIRouter()


def _ticket_out(doc: dict) -> TicketOut:
    return TicketOut(
        id=str(doc["_id"]),
        subject=doc["subject"],
        body=doc["body"],
        customer_tier=doc.get("customer_tier", "free"),
        status=doc.get("status", "pending_review"),
        priority=doc.get("priority"),
        category=doc.get("category"),
        draft_reply=doc.get("draft_reply"),
        reviewer=doc.get("reviewer"),
        review_note=doc.get("review_note"),
        agent_trace=doc.get("agent_trace", []),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )


@router.get("/health", tags=["system"])
async def health(db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    await db.command("ping")
    return {"status": "ok", "service": "agentic-support-triage", "time": datetime.now(timezone.utc).isoformat()}


@router.post("/tickets", response_model=TicketOut, status_code=201, tags=["tickets"])
async def create_ticket(payload: TicketCreate, db: AsyncIOMotorDatabase = Depends(get_db)) -> TicketOut:
    now = utcnow()
    doc = {
        "subject": payload.subject,
        "body": payload.body,
        "customer_tier": payload.customer_tier,
        "status": "pending_review",
        "created_at": now,
        "updated_at": now,
    }
    result = await db.tickets.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _ticket_out(doc)


@router.get("/tickets", response_model=list[TicketOut], tags=["tickets"])
async def list_tickets(db: AsyncIOMotorDatabase = Depends(get_db)) -> list[TicketOut]:
    docs = await db.tickets.find().sort("created_at", -1).to_list(100)
    return [_ticket_out(d) for d in docs]


@router.get("/tickets/{ticket_id}", response_model=TicketOut, tags=["tickets"])
async def get_ticket(ticket_id: str, db: AsyncIOMotorDatabase = Depends(get_db)) -> TicketOut:
    try:
        oid = ObjectId(ticket_id)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid ticket id")
    doc = await db.tickets.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="ticket not found")
    return _ticket_out(doc)


@router.post("/tickets/{ticket_id}/run", response_model=RunOut, tags=["agents"])
async def run_agents(ticket_id: str, db: AsyncIOMotorDatabase = Depends(get_db)) -> RunOut:
    try:
        oid = ObjectId(ticket_id)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid ticket id")
    doc = await db.tickets.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="ticket not found")

    workflow = await run_workflow(doc["body"])
    now = utcnow()
    await db.tickets.update_one(
        {"_id": oid},
        {
            "$set": {
                "status": workflow["status"],
                "priority": workflow["priority"],
                "category": workflow["category"],
                "draft_reply": workflow["draft"],
                "agent_trace": workflow["steps"],
                "updated_at": now,
            }
        },
    )
    return RunOut(
        ticket_id=ticket_id,
        status=workflow["status"],
        steps=workflow["steps"],
        needs_human=workflow["needs_human"],
    )


@router.post("/tickets/{ticket_id}/approval", response_model=TicketOut, tags=["approvals"])
async def approve_ticket(
    ticket_id: str, payload: ApprovalIn, db: AsyncIOMotorDatabase = Depends(get_db)
) -> TicketOut:
    try:
        oid = ObjectId(ticket_id)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid ticket id")
    doc = await db.tickets.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="ticket not found")
    if doc.get("status") not in ("pending_review",):
        raise HTTPException(status_code=409, detail=f"ticket is {doc.get('status')}, not pending_review")

    now = utcnow()
    new_status: TicketStatus = payload.decision
    await db.tickets.update_one(
        {"_id": oid},
        {"$set": {"status": new_status, "reviewer": payload.reviewer, "review_note": payload.note, "updated_at": now}},
    )
    doc.update({"status": new_status})
    return _ticket_out(doc)
