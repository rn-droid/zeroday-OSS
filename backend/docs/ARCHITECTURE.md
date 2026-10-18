# LexiGuard — Architecture Specification

> **System:** LexiGuard / Golden Brown  
> **Status:** Tier 0 Core Architecture Verified  
> **Component Boundaries:** Local-Only FastAPI + SQLite FTS5 + React 19 Frontend + Local Ollama

---

## 1. High-Level Architecture Overview

LexiGuard operates entirely on the user's local machine with strict process separation and loopback-only communication:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        User Web Browser                                │
│                                                                        │
│   ┌──────────────────────────────────────────────────────────────┐    │
│   │                 React 19 + TypeScript SPA                    │    │
│   │  - In-Memory Auth Token (useRef/React Context)               │    │
│   │  - Zero LocalStorage / SessionStorage / Cookies              │    │
│   │  - Self-Contained Assets (Zero CDNs / Remote Fonts)          │    │
│   └──────────────────────────────┬───────────────────────────────┘    │
└──────────────────────────────────┼─────────────────────────────────────┘
                                   │ HTTP (127.0.0.1:8000 only)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     FastAPI Host Process (Python 3.11+)                │
│                                                                        │
│   ┌────────────────────────┐         ┌──────────────────────────────┐  │
│   │ Security Middleware    │         │ Token Store (In-Memory)      │  │
│   │ - Host: 127.0.0.1 check│◄───────►│ - One-time launch code       │  │
│   │ - Security Headers     │         │ - Ephemeral bearer tokens    │  │
│   │ - Cache: no-store      │         └──────────────────────────────┘  │
│   └───────────┬────────────┘                                           │
│               │                                                        │
│               ▼                                                        │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │ API Routers (/api/session, /api/health, /api/documents, /ask)   │  │
│   └───────────┬──────────────────────────────────┬──────────────────┘  │
│               │                                  │                     │
│               ▼                                  ▼                     │
│   ┌───────────────────────────┐      ┌──────────────────────────────┐  │
│   │ Ingestion Pipeline        │      │ Retrieval & Agent Runtime    │  │
│   │ - Magic byte check        │      │ - Router (Classify Intent)   │  │
│   │ - pypdfium2 child runner  │      │ - Lexical FTS5 Engine (BM25) │  │
│   │ - Normalizer & Segmenter  │      │ - Review Engine (Core 10)    │  │
│   │ - Quality & Lang gates    │      │ - Silence / Refusal Detector │  │
│   └───────────┬───────────────┘      │ - Provenance & Claim Checker │  │
│               │                      │ - RenderedAnswer Formatter   │  │
│               ▼                      └───────────┬──────────────────┘  │
│   ┌───────────────────────────┐                  │                     │
│   │ Per-Doc SQLite Databases  │◄─────────────────┘                     │
│   │ data/docs/<id>/doc.sqlite3│                                        │
│   │ - pages, sentences, FTS5  │                                        │
│   └───────────────────────────┘                                        │
└──────────────────────────────────────────────────┼─────────────────────┘
                                                   │ Loopback HTTP
                                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Local Ollama Server                             │
│                  http://127.0.0.1:11434 (Optional)                     │
│                 Model: gemma4:e4b-it-q4_K_M (or e2b)                   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### 2.1 Ingestion & Sandboxing Subsystem (`backend/app/ingest/`)
- **Worker (`worker.py`)**: Coordinates the pipeline from byte ingestion to SQLite commit.
- **Parser (`parser.py`)**: Spawns a sandboxed subprocess executing `pypdfium2`. Enforces strict timeout (15s) and stdout cap (10MB) to prevent decompression bombs.
- **Normalizer (`normalize.py`)**: Normalizes line endings to LF, applies Unicode NFC form, strips null bytes and dangerous escape codes.
- **Segmenter (`segment.py`)**: Uses rule-based regex segmentation to break pages into structural paragraphs and sentences. Derives sentence IDs via `s_<sha256[:12]>`.
- **Quality & Language Gates (`quality.py`, `language.py`)**: Computes character density, alpha-to-symbol ratios, and validates English token frequency to prevent indexing garbled OCR or non-English text without user notice.

### 2.2 Storage & Indexing Subsystem (`backend/app/store/`)
- **Per-Document SQLite DB (`db.py`)**: Every ingested document receives its own SQLite database file under `data/docs/<document_id>/doc.sqlite3`.
- **FTS5 Full-Text Index (`fts.py`)**: Employs SQLite's native FTS5 extension with BM25 ranking over sentence text for sub-millisecond keyword and phrase queries.
- **Safe Deletion (`delete.py`)**: Safely closes database connection pools, unlinks disk artifacts, and verifies directory absence on `DELETE /api/documents/{id}`.

### 2.3 Retrieval Subsystem (`backend/app/retrieval/`)
- **Lexical Search (`lexical.py`)**: Tokenizes queries, applies query expansion using `lexicons/rental_topics.yaml`, searches FTS5, and ranks sentences with reciprocal rank fusion.
- **Silence & Refusal Detector (`silence.py`)**: Identifies out-of-scope, non-contract, or legally prohibitive queries before invoking LLM inference.
- **Core 10 Review Evaluator (`review.py`)**: Deterministically scans documents against the 10 core rental topics (Parties, Term, Rent, Deposit, Notice, Lock-in, Penalties, Restrictions, Maintenance, Disputes) and assigns attention-first priorities.

### 2.4 Agent Runtime & Validation Subsystem (`backend/app/agent/`, `backend/app/validation/`)
- **Bounded State Machine (`runtime.py`)**: A bounded runtime that prevents infinite loops or hallucinated tool usage:
  `RECEIVE -> CLASSIFY -> PLAN -> RETRIEVE -> ANALYZE -> VALIDATE -> RESPOND`.
- **Literal Validator (`literal.py`)**: Enforces exact match of numbers, currencies (Rs./INR), and dates against cited sentences.
- **Provenance Validator (`provenance.py`)**: Rejects any cited sentence ID (`sid`) not present in retrieved context.
- **Legal Policy Validator (`legal_policy.py`)**: Strips judicial predictions, enforces `legal_verdict = None`, and attaches statutory disclaimers.
- **Renderer (`renderer.py`)**: Formats the final validated `RenderedAnswer` response payload.

### 2.5 Security Subsystem (`backend/app/security/`)
- **Token Store (`tokens.py`)**: Ephemeral, in-memory token cache. No secret keys or session tokens are written to disk.
- **Host & Origin Guard (`headers.py`)**: Validates that request `Host` header resolves to `127.0.0.1` or `localhost`, preventing DNS rebinding.
- **Cache Prevention (`headers.py`)**: Attaches `Cache-Control: no-store, no-cache, must-revalidate` and `Pragma: no-cache` to all document endpoints.

---

## 3. Technology Stack & Decision Summary

| Layer | Component | Decision Rationale |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI + Uvicorn | Async performance, strict Pydantic v2 schemas, native OpenAPI generation |
| **PDF Extraction** | `pypdfium2` in child process | Permissive Apache-2.0 / BSD license (avoids AGPL PyMuPDF), C++ sandbox safety |
| **Database** | SQLite + FTS5 | Zero-install, serverless, atomic per-document isolation, robust BM25 ranking |
| **Local Model** | Gemma 4 via Ollama | Open weights, permissive license, native JSON structured outputs, local loopback |
| **Frontend SPA** | React 19 + TypeScript + Vite | Accessible, strict compile-time types, fast local build, zero CDN dependency |
