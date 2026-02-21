# Collaborative AI Agent Framework

A production-grade distributed AI workflow system built with **FastAPI + PostgreSQL + Redis + Celery + LangGraph**.

This system enables **asynchronous multi-agent task execution with human-in-the-loop approval**, structured logging, and full test coverage.

---

# Features

## Core Workflow
- Create task → stored in DB with `PENDING`
- Worker executes research phase → `RUNNING`
- Pauses for human approval → `AWAITING_APPROVAL`
- Resume execution → writing phase
- Final result stored → `COMPLETED`

## Architecture
- **FastAPI** → API layer
- **PostgreSQL** → persistent task storage
- **Redis** → message broker + result backend
- **Celery** → distributed async worker
- **LangGraph-ready** → agent orchestration layer
- **Structured JSON logging** → file + DB audit trail
- **WebSocket-ready** → real-time updates (extensible)

## Testing
- Pytest with **SQLite in-memory DB**
- Deterministic **synchronous worker mode**
- Covers:
  - API contract
  - Workflow lifecycle
  - Integration (result + logs)
  - WebSocket endpoint existence

---
