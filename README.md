# Agentic Support Triage

Multi-agent support triage workflow with tool calling and human-in-the-loop review.

## Architecture

```
Ticket → TriageAgent ──(classify_ticket tool)──► priority/category
       → KnowledgeAgent ──(search_kb, draft_reply)──► draft reply
       → ReviewGate ──► pending_review (human) | auto-approved (low)
```

- **Backend**: FastAPI + motor (async MongoDB), LLM provider abstraction with deterministic mock mode
- **Agents**: TriageAgent → KnowledgeAgent → ReviewGate, full trace stored on every ticket
- **Frontend**: React + Vite + Tailwind — ticket queue, agent run, approve/reject
- **Infra**: docker-compose (MongoDB 7 + api + web), Makefile, GitHub Actions CI

## Quick start

```bash
make up        # builds and starts mongo + api + web
make seed      # inserts 4 sample tickets
# API  → http://localhost:8000/docs
# Web  → http://localhost:5173
make down      # stop
```

## Run tests

```bash
make test      # pytest, in-process, no external services needed
```

## API

| Method | Path | Description |
|---|---|---|
| GET | /api/health | Liveness + Mongo ping |
| POST | /api/tickets | Create ticket |
| GET | /api/tickets | List tickets |
| GET | /api/tickets/{id} | Ticket detail (with agent trace) |
| POST | /api/tickets/{id}/run | Run the agent workflow |
| POST | /api/tickets/{id}/approval | Human approve/reject |
