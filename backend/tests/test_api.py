"""API tests — run fully in-process with a mocked MongoDB."""

import pytest

pytestmark = pytest.mark.asyncio


async def test_health(client):
    res = await client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"


async def test_create_ticket(client):
    res = await client.post(
        "/api/tickets",
        json={"subject": "API returns 500", "body": "The checkout API crashed when paying with a saved card."},
    )
    assert res.status_code == 201
    ticket = res.json()
    assert ticket["status"] == "pending_review"


async def test_agent_run_flags_high_priority_for_human(client):
    created = await client.post(
        "/api/tickets",
        json={"subject": "Webhook failures", "body": "Our webhook integration is broken and events keep failing."},
    )
    tid = created.json()["id"]

    res = await client.post(f"/api/tickets/{tid}/run")
    assert res.status_code == 200
    run = res.json()
    assert run["needs_human"] is True
    assert run["status"] == "pending_review"
    assert any(s["agent"] == "triage" for s in run["steps"])
    assert any(s["agent"] == "knowledge" for s in run["steps"])

    ticket = (await client.get(f"/api/tickets/{tid}")).json()
    assert ticket["priority"] in {"high", "urgent"}
    assert ticket["draft_reply"]


async def test_human_approval_flow(client):
    created = await client.post(
        "/api/tickets",
        json={"subject": "Invoice question", "body": "Question about the invoice charge from last month billing."},
    )
    tid = created.json()["id"]
    await client.post(f"/api/tickets/{tid}/run")

    res = await client.post(
        f"/api/tickets/{tid}/approval",
        json={"decision": "approved", "reviewer": "alice"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "approved"


async def test_low_priority_auto_approval(client):
    created = await client.post(
        "/api/tickets",
        json={"subject": "Feature idea", "body": "It would be nice to have dark mode across the dashboard someday."},
    )
    tid = created.json()["id"]
    res = await client.post(f"/api/tickets/{tid}/run")
    run = res.json()
    assert run["needs_human"] is False
    assert run["status"] == "approved"
