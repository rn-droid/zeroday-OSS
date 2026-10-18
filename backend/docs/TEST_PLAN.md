# LexiGuard — Test Plan & Verification Matrix

> **Testing Scope:** Backend Unit, Retrieval, Model, Agent, Ingestion, Integration, and Frontend Unit/Component Suites.  
> **Backend Test Framework:** `pytest` (70 tests, 100% pass)  
> **Frontend Test Framework:** `vitest` (16 tests, 100% pass)  
> **Total Automated Tests:** 86 Tests

---

## 1. Test Strategy & Structure

```
tests/
├── unit/
│   ├── test_upload_validation.py     # T-ING-VAL-* (magic bytes, size caps, empty files)
│   ├── test_normalize.py             # T-ING-NORM-* (CRLF->LF, NFC, whitespace)
│   ├── test_segment.py               # T-ING-SEG-* (sentence boundaries, sid hashing)
│   ├── test_quality_language.py      # T-ING-QL-* (character density, English heuristics)
│   └── test_statutory_citations.py   # T-STAT-* (India Code sections, statutory context)
├── retrieval/
│   └── test_retrieval.py             # T-RET-* (FTS5 BM25, topic queries, silence gate)
├── model/
│   └── test_ollama_native.py         # T-MOD-* (Ollama client, structured JSON, error states)
├── agent/
│   └── test_vertical.py              # T-AGT-* (route classification, state machine, refusal)
├── evaluation/
│   └── test_evaluation.py            # T-EVAL-* (CUAD QA alignment, latency, coverage)
└── integration/
    ├── test_ingest_pipeline.py       # T-INT-ING-* (end-to-end PDF/TXT parsing to SQLite)
    ├── test_deletion.py              # T-INT-DEL-* (safe deletion, unlinking, directory check)
    ├── test_open_india_law_stress.py # T-INT-STR-* (stress test with complex Indian law text)
    └── test_api_endpoints.py         # T-INT-API-* (full HTTP lifecycle: session, health, doc, ask, review, del)
```

---

## 2. Requirement-to-Test Traceability Matrix

| Test Suite | Test Identifier | Covered Requirement | Verification Method |
| :--- | :--- | :--- | :--- |
| `test_upload_validation.py` | `test_magic_bytes_detection` | FR-ING-01, FR-ING-02 | Verifies `%PDF-` detection and rejection of disguised binaries. |
| `test_upload_validation.py` | `test_file_size_exceeded` | FR-ING-01 | Verifies 413 error when file exceeds 50 MB. |
| `test_normalize.py` | `test_crlf_to_lf` | FR-ING-04 | Confirms canonical LF normalization and NFC Unicode. |
| `test_segment.py` | `test_sentence_id_determinism` | FR-ING-05 | Validates that identical text generates identical `sid`. |
| `test_quality_language.py` | `test_unreadable_page_flag` | FR-ING-06 | Flags pages with low character density or garbled tokens. |
| `test_retrieval.py` | `test_fts5_bm25_search` | FR-STR-02 | Confirms BM25 keyword matching over sentence index. |
| `test_retrieval.py` | `test_silence_on_irrelevant` | FR-ASK-02 | Verifies refusal on irrelevant non-contract queries. |
| `test_ollama_native.py` | `test_generate_structured_json`| FR-ASK-03 | Tests JSON parsing and schema validation from local model. |
| `test_vertical.py` | `test_legal_verdict_refusal` | FR-ASK-03 | Validates `legal_verdict = None` and `recommend_professional_review = True`. |
| `test_statutory_citations.py` | `test_india_code_context` | FR-ASK-04 | Tests citation of Transfer of Property Act & Easements Act. |
| `test_deletion.py` | `test_safe_deletion_and_verify` | FR-STR-03 | Verifies DB close, directory unlinking, and forensic note. |
| `test_api_endpoints.py` | `test_api_full_lifecycle` | FR-SEC-01 - 04, FR-REV-01 | Full end-to-end integration test across all 8 REST endpoints. |

---

## 3. Frontend Test Inventory (`frontend/src/test/`)

| Test File | Test Case | Covered Feature |
| :--- | :--- | :--- |
| `session.test.ts` | `extracts and removes launch code from URL fragment` | FR-SEC-02 (Fragment stripping) |
| `session.test.ts` | `returns null when no launch code present` | FR-SEC-01 (Clean URL fallback) |
| `privacy.test.ts` | `verifies zero localStorage or sessionStorage usage` | FR-SEC-04 (No storage leak) |
| `privacy.test.ts` | `verifies no external CDN links or remote fonts` | FR-SEC-04 (Local isolation) |
| `components.test.tsx` | `renders StatusLabel with semantic color and accessibility` | FR-UI-01 (Accessible UI) |
| `components.test.tsx` | `renders SourceCitation and triggers page modal` | FR-UI-02 (Verbatim quotes) |
| `api-client.test.ts` | `exchanges launch code in mock and live clients` | FR-SEC-03 (Token bootstrap) |
| `api-client.test.ts` | `handles question answering with legal boundaries` | FR-ASK-03 (Zero verdicts) |
| `api-client.test.ts` | `handles conflicting clauses in rental agreement` | FR-REV-02 (Dual citations) |
| `api-client.test.ts` | `prevents question greater than 500 characters` | FR-ASK-01 (500-char limit) |
| `api-client.test.ts` | `handles document deletion truthfully` | FR-STR-03 (Truthful deletion) |

---

## 4. Execution Commands

```bash
# Run backend test suite (all 70 tests)
cd backend
pytest

# Run frontend test suite (all 16 tests)
cd frontend
npm test

# Run frontend linter
npm run lint

# Run frontend production build
npm run build
```
