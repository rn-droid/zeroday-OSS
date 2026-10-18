# TASKS.md — LexiGuard Implementation Tracker

## Active Tier: Tier 0 (Submittable Core) + Tier 1 Extensions

> **Status:** All Tier 0 & Tier 1 Core Requirements Fully Implemented & Verified.  
> **Backend Tests:** 70 passed in `pytest` (100% pass).  
> **Frontend Tests:** 16 passed in `vitest` (100% pass).  
> **Evaluation Benchmark:** 81.7% verbatim coverage against CUAD queries; 0 external dispatches.

---

## Phase 0 — INSPECT, FREEZE, DOCUMENT

**Status: COMPLETED**

- [x] Inspect repo (branch, tree, .gitignore, LICENSE, README)
- [x] Replace README with honest status README
- [x] Create NOTICE
- [x] Create AGENTS.md
- [x] Create TASKS.md
- [x] Create pyproject.toml
- [x] Create CONTRIBUTING.md
- [x] Create CODE_OF_CONDUCT.md
- [x] Update .gitignore
- [x] Create docs/REQUIREMENTS.md
- [x] Create docs/ARCHITECTURE.md
- [x] Create docs/DATA_FLOW.md
- [x] Create docs/PRIVACY.md
- [x] Create docs/LIMITATIONS.md
- [x] Create docs/MODEL.md
- [x] Create docs/MODEL_SETUP.md
- [x] Create docs/MODEL_LICENSE.md
- [x] Create docs/EVALUATION.md
- [x] Create docs/TEST_PLAN.md
- [x] Create docs/adr/ (ADR-0001 through ADR-0010)
- [x] Create Makefile scaffold
- [x] Create CI scaffold (.github/workflows/ci.yml)

---

## Phase 1 — INGESTION & STORAGE

**Status: COMPLETED**

### 1.1 FastAPI Skeleton & Security
- [x] backend/app/main.py — app factory, static serving, startup launch URL, lifecycle
- [x] backend/app/config.py — settings (Pydantic v2 Settings)
- [x] backend/app/security/ — tokens, host/origin validation, security & cache-control headers
- [x] backend/app/api/ — route handlers (/api/session, /api/health, /api/documents)

### 1.2 Upload Validation & Ingestion Pipeline
- [x] backend/app/ingest/upload.py — magic bytes, size limits (50 MB), page cap, encoding
- [x] backend/app/ingest/worker.py — orchestrate ingestion pipeline
- [x] backend/app/ingest/parser.py — child-process pypdfium2 runner with watchdog timeout & output cap
- [x] backend/app/ingest/normalize.py — CRLF to LF, Unicode NFC normalization, whitespace collapsing
- [x] backend/app/ingest/segment.py — page -> headings -> paragraphs -> sentences + deterministic sid generation
- [x] backend/app/ingest/quality.py — per-page quality gate (character density, printable ratios)
- [x] backend/app/ingest/language.py — per-page language gate (English token frequency heuristics)

### 1.3 Per-Document SQLite / FTS5 Store
- [x] backend/app/store/db.py — connection factory, PRAGMA setup (WAL, secure_delete=ON)
- [x] backend/app/store/documents.py — document table CRUD
- [x] backend/app/store/pages.py — pages table
- [x] backend/app/store/sentences.py — sentences table
- [x] backend/app/store/fts.py — FTS5 index helpers with BM25 ranking
- [x] backend/app/store/delete.py — safe deletion service verifying file and directory removal

### 1.4 Ingestion Tests (T-ING-*)
- [x] tests/unit/test_upload_validation.py (8 passed)
- [x] tests/unit/test_normalize.py (6 passed)
- [x] tests/unit/test_segment.py (7 passed)
- [x] tests/unit/test_quality_language.py (9 passed)
- [x] tests/integration/test_ingest_pipeline.py (5 passed)
- [x] tests/integration/test_deletion.py (3 passed)

---

## Phase 2 — OLLAMA ADAPTER & MODEL MANAGEMENT

**Status: COMPLETED**

- [x] backend/app/model/ollama_native.py — async native Ollama client (`/api/generate`, `/api/tags`)
- [x] backend/app/model/provider.py — model provider abstraction and model configuration
- [x] Pinned models: `gemma4:e4b-it-q4_K_M` (primary) and `gemma4:e2b-it-q4_K_M` (lightweight fallback)
- [x] tests/model/test_ollama_native.py (8 passed)

---

## Phase 3 — RETRIEVAL & REVIEW EVALUATOR

**Status: COMPLETED**

- [x] backend/app/retrieval/lexical.py — BM25 full-text search with query expansion from rental topics
- [x] backend/app/retrieval/silence.py — silence gate and refusal logic for out-of-scope queries
- [x] backend/app/retrieval/review.py — Core 10 rental topics evaluation with attention-first risk ordering
- [x] backend/lexicons/rental_topics.yaml — curated rental domain topics and keywords
- [x] backend/lexicons/statutory_context.yaml — Indian tenancy law context (Transfer of Property Act, Easements Act, Model Tenancy Act)
- [x] tests/retrieval/test_retrieval.py (9 passed)
- [x] tests/unit/test_statutory_citations.py (3 passed)

---

## Phase 4 — VERTICAL SLICE & AGENT RUNTIME

**Status: COMPLETED**

- [x] backend/app/agent/router.py — query intent classifier (CUAD, factual, conflict, statutory, legal verdict)
- [x] backend/app/agent/runtime.py — bounded state machine runtime (max 8 tool calls, max 4 model calls)
- [x] backend/app/validation/literal.py — strict number, currency, and date verification against source text
- [x] backend/app/validation/provenance.py — validates that all cited sentence IDs were retrieved during the turn
- [x] backend/app/validation/legal_policy.py — enforces `legal_verdict = None` and adds legal disclaimers
- [x] backend/app/validation/renderer.py — formats final RenderedAnswer payload
- [x] tests/agent/test_vertical.py (8 passed)

---

## Phase 5 — EVALUATION & BENCHMARKING

**Status: COMPLETED**

- [x] tests/evaluation/ground_truth_questions.json — CUAD-aligned evaluation queries
- [x] tests/evaluation/evaluate_core.py — benchmark runner computing verbatim coverage, latency, token counts
- [x] tests/evaluation/test_evaluation.py (2 passed)
- [x] Benchmark report: `docs/reports/eval_results.json` (81.7% verbatim snippet coverage, 6.26 ms avg latency)

---

## Phase 6 — PRIVACY AUDIT & NETWORK ISOLATION

**Status: COMPLETED**

- [x] scripts/run_privacy_audit.sh — loopback-only network isolation verification
- [x] Verified zero external calls, zero telemetry, zero cloud fallback
- [x] Audit report: `docs/reports/network_isolation.log`

---

## Phase 7 — FRONTEND IMPLEMENTATION

**Status: COMPLETED**

- [x] React 19 + TypeScript + Vite architecture with self-contained assets (zero CDNs/remote fonts)
- [x] One-time launch code extraction (`#k=...`) & in-memory Bearer token auth (`useRef`)
- [x] In-memory AppStateProvider without browser storage persistence
- [x] UploadView, DocumentListView, OverviewView (Core 10 cards)
- [x] AskView with 500-character limit & RenderedAnswerView with claim classification badges
- [x] ReviewView with attention-first risk ordering, dual conflict citations, and neutral professional questions
- [x] SourceViewer modal with physical page numbers and verbatim quote highlighting
- [x] DeleteModal with truthful distinction between app file removal and forensic SSD erasure
- [x] FRONTEND_API_CONTRACT_GAPS.md — complete contract register and reconciliation
- [x] Frontend Vitest suite: 16 passed tests (100% pass)
- [x] Production bundle build (`dist/`) mounted on FastAPI root

---

## Phase 8 — END-TO-END API INTEGRATION

**Status: COMPLETED**

- [x] tests/integration/test_api_endpoints.py (1 passed comprehensive lifecycle test):
  - POST /api/session (launch code exchange)
  - GET /api/health (token check)
  - POST /api/documents (upload and ingestion)
  - GET /api/documents (document listing)
  - GET /api/documents/{id}/pages/1 (source page retrieval)
  - POST /api/documents/{id}/ask (CUAD Parties & Governing Law questions)
  - POST /api/documents/{id}/ask (legal enforceability refusal scanner)
  - POST /api/documents/{id}/review & GET /api/documents/{id}/overview (Core 10 topics)
  - DELETE /api/documents/{id} (verified deletion and 404 confirmation)
- [x] tests/integration/test_open_india_law_stress.py (1 passed)
