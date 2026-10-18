# LexiGuard — Privacy, Security & Data Isolation Architecture

> **Security Posture:** Zero-Trust Local-Only Architecture  
> **Network Boundary:** Loopback (`127.0.0.1`) Only  
> **Verification Status:** Audited via `scripts/run_privacy_audit.sh` & Verified in `reports/network_isolation.log`

---

## 1. Privacy First Principles

Legal agreements—especially tenancy, residential lease, and leave-and-licence agreements—contain sensitive Personally Identifiable Information (PII) including full names, permanent addresses, Aadhaar/PAN references, bank account numbers, phone numbers, and rental financial terms. 

LexiGuard is architected from the ground up on the principle of **absolute local isolation**:
1. **Zero External Calls:** Under no circumstance does document text, query text, metadata, or telemetry leave the local device.
2. **Zero Cloud Fallback:** If local Ollama or the local parser is unavailable, operations fail closed with a clear status message. No remote API fallback exists.
3. **Zero Persistent Browser Storage:** The web frontend stores zero tokens, documents, or answers in browser-persisted caches (`localStorage`, `sessionStorage`, `indexedDB`, cookies).
4. **Verified Local Deletion:** All derived data can be completely purged on demand.

---

## 2. Technical Privacy Guarantees

### 2.1 Network Binding & Loopback Isolation
- The FastAPI application binds exclusively to `127.0.0.1` (or user-specified local loopback). It never binds to `0.0.0.0` or public network interfaces.
- Host header validation rejects any HTTP request whose `Host` header is not `127.0.0.1` or `localhost`, eliminating DNS rebinding attacks.
- Outbound network requests are prevented. The application makes no external API calls, DNS queries, or update checks.
- Audit evidence is documented in `backend/docs/reports/network_isolation.log`.

### 2.2 In-Memory Session Bootstrap
- The backend produces an ephemeral one-time launch code upon startup and prints the launch URL (`http://127.0.0.1:8000/#k=<code_hex>`).
- The code is carried in the URL fragment `#k=...` (never sent over the wire in HTTP request paths or query strings).
- On page load, the frontend immediately reads `#k=...` and calls `history.replaceState` to strip it from the URL bar before exchanging it via `POST /api/session`.
- The returned Bearer token is held only in a React Context `useRef` in active browser memory.
- Closing or refreshing the tab clears the token instantly. Subsequent calls receive `401 Unauthorized`.

### 2.3 Cache Prevention & Security Headers
All API responses that handle document content, page excerpts, questions, or answers include strict cache-prevention headers:
```http
Cache-Control: no-store, no-cache, must-revalidate
Pragma: no-cache
Expires: 0
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'
```

### 2.4 Per-Document Database Isolation
- Every document is stored in an isolated SQLite database file under `data/docs/<document_id>/doc.sqlite3`.
- No global cross-document table or shared index exists.
- Ingestion enforces PRAGMA `secure_delete=ON`, ensuring that deleted SQLite rows are overwritten with zeroes rather than simply marked as free space.

### 2.5 Deletion vs. Forensic Erasure Distinction
When a user deletes a document via `DELETE /api/documents/{id}`:
- Backend closes all open connections to `doc.sqlite3`.
- Directory `data/docs/<document_id>` and all child files are unlinked.
- Frontend purges all references from memory.
- The system returns an explicit forensic disclosure:
  > *"App-controlled files removed. This does NOT constitute forensic erasure from SSD, OS swap, or external backups. See docs/LIMITATIONS.md."*

---

## 3. Privacy Audit Verification

The repository includes an automated privacy audit script: `scripts/run_privacy_audit.sh`.
The audit validates:
- Process socket binding is restricted to `127.0.0.1`.
- Zero HTTP requests are dispatched to external domains during full test suite runs.
- Frontend bundle contains zero references to external script tags, font links, or CDN URLs.
