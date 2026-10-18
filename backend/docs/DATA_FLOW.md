# LexiGuard — Data Flow & Lifecycle Specification

> **Specification Basis:** Solution Guide v3.1, Final Requirements v3.2.  
> **Status:** Tier 0 Lifecycle Verified.

---

## 1. End-to-End Data Flow Stages

```
[Document Upload (PDF/TXT)]
         │
         ▼
[1. Magic Byte & Size Validation] ──(fail)──► HTTP 413 / 422
         │
         ▼
[2. Sandboxed PDF Parser Subprocess] ──(timeout/corrupt)──► Partial / Incomplete Ingest
         │
         ▼
[3. Text Normalization (NFC / LF)]
         │
         ▼
[4. Segmentation & Sentence ID Hashing]
         │
         ▼
[5. Quality & Language Gates]
         │
         ▼
[6. SQLite Commit (Pages, Sentences, FTS5 Index)]
         │
         ▼
[7. Core 10 Topic Evaluation & Risk Ordering]
         │
         ▼
[User Query Input] ──► [8. Router Classification]
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   [Direct Fast-Path]                 [FTS5 Lexical Retrieval]
            │                                 │
            │                                 ▼
            │                        [Candidate Sentences]
            │                                 │
            │                                 ▼
            │                        [Candidate Validation & Scoring]
            │                                 │
            └────────────────┬────────────────┘
                             │
                             ▼
               [9. Deterministic Claim Validation]
               - Literal Number/Date Matching
               - Provenance Verification
               - Legal Verdict Nullification
                             │
                             ▼
               [10. Rendered Answer Output (JSON)]
                             │
                             ▼
               [User Deletes Document]
                             │
                             ▼
               [11. Safe Deletion & State Purge]
```

---

## 2. Detailed Lifecycle Stages

### Stage 1: Ingestion & Upload (`POST /api/documents`)
1. Client submits file via `multipart/form-data` with `"file"` parameter.
2. Ingestion gate verifies file size is within `max_upload_bytes` (50 MB).
3. Magic bytes are checked (`%PDF-` for PDF, printable ASCII/UTF-8 for TXT).
4. For PDFs, the file bytes are written to an isolated temporary spool file and passed to a child Python runner executing `pypdfium2`.
5. The child process extracts text per page with a strict 15-second wall clock timer.

### Stage 2: Normalization, Segmentation & Gating
1. Raw page strings are normalized: Unicode normalized to NFC, Windows `\r\n` converted to `\n`, multiple spaces collapsed.
2. Sentences are segmented using boundary heuristics.
3. Every sentence receives a deterministic identifier: `s_<sha256(text.strip().lower())[:12]>`.
4. Page quality gate inspects printable character ratio (threshold > 0.85) and character density.
5. Language gate evaluates token overlap with English stopword lexicons.

### Stage 3: Indexing & Storage
1. A unique SHA-256 hash of the normalized document text establishes `document_id`.
2. A per-document directory is created: `data/docs/<document_id>/`.
3. Database `doc.sqlite3` is initialized with PRAGMA `journal_mode=WAL` and `synchronous=NORMAL`.
4. Tables populated: `document`, `pages`, `sentences`, and the FTS5 virtual table `sentences_fts`.
5. Ingestion returns `UploadResponse` with `document_id`, `page_count`, quality metrics, and warnings.

### Stage 4: Core 10 Risk Review (`POST /api/documents/{id}/review`)
1. Review engine loads `lexicons/rental_topics.yaml`.
2. For each of the Core 10 topics (Parties, Term, Rent, Deposit, Notice, Lock-in, Penalties, Restrictions, Maintenance, Disputes), FTS5 queries retrieve candidate clauses.
3. Cross-clause comparison detects potential conflicts (e.g., Clause 5 stating 30 days notice vs. Clause 8 stating 60 days notice).
4. Review topics are prioritized using deterministic attention-first ranking:
   - Conflicts first (flagged with dual evidence citations).
   - Ambiguities & non-standard lock-in/penalty clauses next.
   - Standard located clauses.
   - Clauses not located in document.

### Stage 5: Interactive Querying & Answer Rendering (`POST /api/documents/{id}/ask`)
1. User submits question up to 500 characters.
2. Router classifies query intent into routes (`CUAD_POINT`, `FACTUAL`, `CONFLICT_CHECK`, `STATUTORY`, `LEGAL_CONCLUSION`, `OUT_OF_SCOPE`).
3. For factual queries, lexical search gathers relevant sentences, deduplicates, and passes top hits to the model or deterministic extractor.
4. Model generates structured proposal containing claims, interpretations, concerns, or ambiguities.
5. Validators run sequentially:
   - **Literal Validator**: Verifies that numbers, currency amounts, and dates in the claims match cited sentences exactly.
   - **Provenance Validator**: Confirms that cited `sid` values exist in the search result set.
   - **Legal Policy Validator**: Forces `legal_verdict = None` and injects legal disclaimer.
6. Server returns `RenderedAnswer` JSON payload to the frontend.

### Stage 6: Safe Deletion (`DELETE /api/documents/{id}`)
1. Client requests document deletion.
2. Backend closes all active SQLite connections for the target document.
3. The per-document directory `data/docs/<document_id>` and all child files (`doc.sqlite3`, `doc.sqlite3-wal`, etc.) are unlinked from disk.
4. System verifies that `os.path.exists()` returns `False`.
5. Frontend clears all in-memory references, cached page text, questions, and answers.
6. Backend responds with `DeleteResponse` containing truthful limitations note.
