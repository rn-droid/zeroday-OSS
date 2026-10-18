# LexiGuard (Golden Brown)

**Private, evidence-backed legal-document triage — ZeroDay OSS Hacktoberfest 2026, Problem Statement 2 (PS2)**

> **Status: Tier 0 Core & Frontend Implemented & Fully Verified.**  
> **Backend Test Suite:** 70 passed in `pytest` (100% passing).  
> **Frontend Test Suite:** 16 passed in `vitest` (100% passing).  
> **Benchmark Performance:** 81.7% verbatim snippet coverage on CUAD extractive QA; 6.26 ms avg lexical retrieval latency; 0 external network calls.  
> **Privacy Posture:** 100% on-device local loopback (`127.0.0.1`); zero cloud fallback; zero CDNs; zero persistent browser storage.

---

## What LexiGuard Does

LexiGuard helps non-lawyers understand what an English residential rental or leave-and-licence agreement says:

- **100% On-Device Ingestion:** Upload PDF or TXT agreements. Text is extracted locally using `pypdfium2` in a sandboxed child process with a 15-second watchdog and output buffer caps.
- **Fast-Path Lexical Indexing:** Builds a dedicated per-document SQLite database with FTS5 BM25 full-text indexing.
- **Evidence-Backed Q&A:** Answers user queries citing exact sentence IDs (`sid`), physical page numbers (1-based), and immutable verbatim quotes.
- **Attention-First Risk Review:** Evaluates documents across the Core 10 rental topics (Parties, Term, Rent, Deposit, Notice, Lock-in, Penalties, Restrictions, Maintenance, Disputes). Contradictory clauses (such as conflicting 30-day vs. 60-day notice periods) are highlighted at the very top with side-by-side dual citations.
- **Neutral Professional Questions:** Prepares objective, non-accusatory questions for users to review with a qualified lawyer or landlord.
- **Statutory Context:** Seamlessly cites Indian tenancy legal frameworks (Transfer of Property Act 1882, Indian Easements Act 1882, Model Tenancy Act 2021) without hallucinating contract terms.
- **Strict Legal Refusal:** Permanently locks `legal_verdict = null`. Detects queries seeking legal conclusions or judicial predictions and returns `LEGAL_LIMIT` with professional consultation notices.
- **Verified Safe Deletion:** Purges all SQLite rows, closes active connections, unlinks directory trees, and clears frontend memory, while honestly distinguishing application file removal from forensic SSD erasure.

---

## Architectural Choices & Locked Technology Stack

| Concern | Component / Decision | Rationale |
| :--- | :--- | :--- |
| **Backend** | Python 3.11+ / FastAPI / Uvicorn | High-performance async ASGI server bound to `127.0.0.1` |
| **Frontend** | React 19 / TypeScript / Vite | Single Page Application with zero CDNs, zero cookies, and zero localStorage |
| **PDF Extraction**| `pypdfium2` in child process | Permissive Apache-2.0 / BSD license; eliminates AGPL PyMuPDF risks |
| **Storage** | Per-document SQLite + FTS5 | Serverless, zero-install, PRAGMA `secure_delete=ON`, WAL mode |
| **Local Model** | Gemma 4 (`gemma4:e4b-it-q4_K_M`) via Ollama | Open weights, structured JSON support, local loopback inference |
| **Agent Runtime**| Deterministic bounded state machine | Max 8 tool calls, max 4 model calls; Hermes agent framework intentionally omitted (ADR-0010) |
| **License** | Apache-2.0 | Permissive open-source license |

---

## Quickstart & Setup

### 1. Prerequisites

- Python 3.11 or higher.
- Node.js 20 or higher.
- (Optional, for local LLM inference) Ollama ≥ 0.21.1:
  ```bash
  ollama pull gemma4:e4b-it-q4_K_M
  ```
  *(Note: LexiGuard includes a deterministic fast-path retrieval engine that functions even without Ollama running).*

### 2. Backend Setup & Run

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# Install dependencies in editable mode
pip install -e ".[dev]"

# Run the FastAPI server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Upon startup, the server prints a one-time launch URL to the console:
```
============================================================
  LexiGuard is running.
  Open this URL in your browser (valid for 120s):
  http://127.0.0.1:8000/#k=7b3f91...
============================================================
```

### 3. Frontend Setup & Build

The frontend is built and mounted directly on the root of the FastAPI server:

```bash
cd frontend
npm install
npm run build
```

Alternatively, to run the standalone Vite development server with mock API support:
```bash
cd frontend
npm run dev
```

---

## Running the Automated Test Suites

```bash
# Backend pytest suite (70 tests)
cd backend
pytest

# Frontend vitest suite (16 tests)
cd frontend
npm test

# Run CUAD benchmark evaluation
cd backend
python tests/evaluation/evaluate_core.py
```

---

## Documentation Index

- [Requirements Specification](docs/REQUIREMENTS.md)
- [System Architecture](docs/ARCHITECTURE.md)
- [Data Flow & Lifecycle](docs/DATA_FLOW.md)
- [Privacy & Network Isolation](docs/PRIVACY.md)
- [Limitations & Scope Report](docs/LIMITATIONS.md)
- [Model Specification](docs/MODEL.md)
- [Model Setup Guide](docs/MODEL_SETUP.md)
- [Model License Notice](docs/MODEL_LICENSE.md)
- [Evaluation Report](docs/EVALUATION.md)
- [Test Plan & Verification Matrix](docs/TEST_PLAN.md)
- [Reference Datasets Documentation](docs/DATASETS.md)
- [Frontend API Contract Register](frontend/FRONTEND_API_CONTRACT_GAPS.md)
- [Architectural Decision Records (ADR 0001–0010)](docs/adr/)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)

---

## Licence

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).  
Gemma model license: See [docs/MODEL_LICENSE.md](docs/MODEL_LICENSE.md).