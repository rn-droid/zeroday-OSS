# ADR-0001: Selection of FastAPI for Backend Service

## Status
Accepted

## Context
LexiGuard requires a high-performance local web service to coordinate document ingestion, SQLite FTS5 queries, model inference, and secure session management. We considered Flask, Django, and FastAPI.

## Decision
We chose **FastAPI** (backed by `uvicorn` and `pydantic` v2).

## Consequences
- **Advantages:** Native async support for non-blocking I/O during child process execution; automatic request validation with Pydantic; automatic OpenAPI contract generation.
- **Trade-offs:** Requires running within an ASGI server (`uvicorn`); slightly higher initial dependency footprint than bare WSGI.
