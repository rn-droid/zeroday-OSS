# ADR-0004: Ollama Native REST API for Local Inference

## Status
Accepted

## Context
Running local models can be done via raw `llama.cpp` bindings, OpenAI-compatible proxy endpoints, or Ollama's native API (`/api/generate`, `/api/chat`).

## Decision
We chose Ollama's **native REST API** via async `httpx`.

## Consequences
- **Direct Schema Control:** Native endpoints support `format: "json"` with direct temperature, top_p, and context window configuration without intermediate compatibility shims.
- **Fail-Closed Availability Checks:** LexiGuard queries `http://127.0.0.1:11434/api/tags` on startup to confirm model availability; if absent, it safely falls back to lexical fast-path without crashing.
