# LexiGuard — Requirements Specification

> **Specification Basis:** Solution Guide v3.1, Final Requirements v3.2, ZeroDay OSS Hacktoberfest 2026 Problem Statement 2 (PS2).  
> **Target Tier:** Tier 0 (Deterministic Submittable Core) + Tier 1 Extensions.  
> **Status:** Fully Specified & Verified.

---

## 1. System Vision & Problem Statement

Residential rental and leave-and-licence agreements in India often contain ambiguous, asymmetric, or conflicting terms (e.g., conflicting notice periods, undisclosed penalties, restrictive lock-in clauses, or arbitrary deposit deductions). Non-lawyer tenants and owners face severe information asymmetry when reviewing these multi-page legal documents.

**LexiGuard** (code name *Golden Brown*) is an on-device, private legal document triage assistant. It parses agreements locally, indexes their clauses with SQLite FTS5, detects risks and ambiguities in an attention-first hierarchy, enables natural language Q&A backed by immutable verbatim citations, and assists users in preparing neutral questions for qualified legal professionals.

---

## 2. Core Operational Constraints

1. **Strict On-Device Privacy (Zero External Calls):**
   - No document content, page text, question, answer, embedding, or telemetry may leave `127.0.0.1`.
   - The frontend must contain zero CDN dependencies, Google Fonts, or external scripts.
   - All browser session state must remain purely in-memory; zero use of `localStorage`, `sessionStorage`, `indexedDB`, or cookies.

2. **No Legal Advice or Verdicts (Fail-Closed Policy):**
   - The system must never pronounce on whether a contract or clause is "valid", "illegal", "binding", or "enforceable".
   - `legal_verdict` must strictly return `null` in all responses.
   - Any query requesting legal conclusions or external law must trigger a clear professional legal consultation disclaimer.

3. **Verbatim Evidence Gating:**
   - Every substantive claim must be supported by an immutable, verbatim excerpt citing the physical page number (1-based) and sentence ID (`sid`).
   - If evidence cannot be located, the system must truthfully state *"Not located in document"* rather than asserting absence or hallucinating provisions.

4. **Deterministic Core Runtime:**
   - The core runtime uses a bounded state machine with strict turn ceilings (max 8 tool calls, max 4 model calls).
   - In Tier 0, execution defaults to deterministic lexical retrieval over SQLite FTS5. Multi-turn unconstrained agentic frameworks (Hermes) are omitted to guarantee deterministic behavior.

---

## 3. Functional Requirements

### 3.1 Session Bootstrap & Security
- **FR-SEC-01**: Upon startup, the backend generates a cryptographically random one-time launch code valid for a configurable TTL (default 120s).
- **FR-SEC-02**: The frontend extracts `#k=<code>` from the URL fragment on mount and strips it from the browser address bar immediately.
- **FR-SEC-03**: The launch code is exchanged via `POST /api/session` for an in-memory Bearer token.
- **FR-SEC-04**: All subsequent API calls require `Authorization: Bearer <token>` and enforce `Cache-Control: no-store`.

### 3.2 Ingestion & Document Processing
- **FR-ING-01**: Accept PDF (`application/pdf`) and plain text (`text/plain`) files up to 50 MB and 50 pages.
- **FR-ING-02**: Validate magic bytes (`%PDF-`) rather than file extension.
- **FR-ING-03**: Parse PDF text in a dedicated child process with watchdog timeout (15s) and maximum output size (10 MB).
- **FR-ING-04**: Normalize extracted text (CRLF to LF, Unicode NFC normalization, whitespace collapsing).
- **FR-ING-05**: Segment text into physical pages, paragraphs, and sentences with deterministic cryptographic sentence IDs (`s_<hash>`).
- **FR-ING-06**: Execute quality gates (minimum character density, printable ASCII/Unicode ratio) and language checks (English token heuristics). Reject or flag substandard pages.

### 3.3 Storage & Lexical Indexing
- **FR-STR-01**: Maintain per-document isolated SQLite databases located under `data/docs/<document_id>/doc.sqlite3`.
- **FR-STR-02**: Build FTS5 full-text indices with BM25 ranking across document sentences.
- **FR-STR-03**: Support safe deletion via `DELETE /api/documents/{id}`, closing SQLite connections, unlinking disk files, and verifying directory removal.

### 3.4 Question Answering & Claim Verification
- **FR-ASK-01**: Support natural language queries up to 500 characters.
- **FR-ASK-02**: Execute bounded retrieval combining query terms and curated rental topic lexicons (`lexicons/rental_topics.yaml`).
- **FR-ASK-03**: Verify all claims against cited quotes: literal numbers, monetary amounts, dates, and party roles must match source text.
- **FR-ASK-04**: Detect statutory questions and inject curated Indian tenancy law context (Transfer of Property Act 1882, Indian Easements Act 1882, Model Tenancy Act 2021) with statutory disclaimers.

### 3.5 Core 10 Rental Review & Attention-First Ordering
- **FR-REV-01**: Automatically evaluate agreements across Core 10 rental topics: Parties, Term, Rent, Deposit, Notice, Lock-in, Penalties, Restrictions, Maintenance, Disputes.
- **FR-REV-02**: Sort review topics in attention-first risk order:
  1. Possible Conflicts (with dual clause citations)
  2. Ambiguities & non-standard clauses
  3. Monetary & lock-in obligations
  4. Jurisdiction & dispute clauses
  5. Standard found provisions
  6. Not located
  7. Not assessed
- **FR-REV-03**: Provide neutral, non-accusatory questions for users to present to landlords or lawyers.

### 3.6 Frontend User Interface
- **FR-UI-01**: Built with React 19 + TypeScript + Vite with responsive, accessible layout.
- **FR-UI-02**: Document list, upload dropzone, Core 10 overview, interactive Q&A view with claim classification badges, risk review dashboard, and modal source viewer with verbatim highlight matching.
- **FR-UI-03**: Full deletion confirmation dialog stating truthful distinction between application file removal and forensic SSD erasure.

---

## 4. Non-Functional Requirements

- **NFR-LAT-01**: Average lexical retrieval query latency under 50 ms.
- **NFR-MEM-01**: Peak memory footprint of backend process under 200 MB during Tier 0 operations.
- **NFR-ACC-01**: WCAG 2.1 AA compliant color contrast and keyboard navigation throughout the UI.
- **NFR-REL-01**: Zero crash on unreadable or adversarial PDFs; graceful fallback to `INSUFFICIENT_EVIDENCE`.
- **NFR-AUD-01**: 100% test coverage of security boundaries and lifecycle routes.
