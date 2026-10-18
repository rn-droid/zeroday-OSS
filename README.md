# LexiGuard (Golden Brown)

**Private, Evidence-Backed Legal Document Triage — ZeroDay OSS Hacktoberfest 2026, Problem Statement 2 (PS2)**

> **Status: Tier 0 Core & Frontend Implemented & Fully Verified.**  
> **Backend Test Suite:** 70 passed in `pytest` (100% passing).  
> **Frontend Test Suite:** 16 passed in `vitest` (100% passing).  
> **Benchmark Performance:** 81.7% verbatim snippet coverage on CUAD extractive QA; 6.26 ms avg lexical retrieval latency; 0 external network calls.  
> **Privacy Posture:** 100% on-device local loopback (`127.0.0.1`); zero cloud fallback; zero CDNs; zero persistent browser storage.

---

## Repository Structure

```
new/
├── backend/                  # FastAPI ASGI application, storage, retrieval, agent & tests
│   ├── backend/app/          # Core backend packages (api, ingest, store, retrieval, agent, validation)
│   ├── docs/                 # Complete architecture, requirements, evaluation, and ADR specifications
│   │   ├── adr/              # ADR-0001 through ADR-0010
│   │   ├── reports/          # Verified evaluation & network isolation logs
│   │   ├── ARCHITECTURE.md
│   │   ├── DATASETS.md
│   │   ├── EVALUATION.md
│   │   ├── LIMITATIONS.md
│   │   ├── PRIVACY.md
│   │   └── REQUIREMENTS.md
│   ├── fixtures/             # Synthetic test rental agreements (synthetic only, no real agreements)
│   ├── lexicons/             # Rental topics & statutory context YAML lexicons
│   ├── tests/                # Full pytest test suite (unit, integration, retrieval, agent, evaluation)
│   ├── pyproject.toml        # Backend build configuration & dependencies
│   └── TASKS.md              # Detailed implementation tracker
├── frontend/                 # React 19 + TypeScript + Vite Single Page Application
│   ├── src/                  # Components, features, API client, in-memory auth & state
│   ├── dist/                 # Production pre-compiled static assets
│   ├── FRONTEND_API_CONTRACT_GAPS.md # Reconciled API contract register
│   └── package.json          # Frontend build configuration & scripts
└── data/                     # Local document storage (data/docs/<doc_id>/doc.sqlite3)
```

---

## Quickstart

### 1. Launch the Backend Server

```bash
cd backend
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Upon launch, the server emits a secure, one-time URL containing an authentication fragment:
```
============================================================
  LexiGuard is running.
  Open this URL in your browser (valid for 120s):
  http://127.0.0.1:8000/#k=<one_time_token>
============================================================
```

### 2. Access the Application

Open the emitted URL in any modern browser. The frontend extracts the one-time launch code, stores an ephemeral Bearer token in memory, and immediately strips the code from the address bar.

---

## Verification & Testing

```bash
# Run backend tests (70 passed)
cd backend
pytest

# Run frontend tests (16 passed)
cd ../frontend
npm test

# Build frontend bundle
npm run build
```

---

## License

Licensed under the Apache License, Version 2.0. See [backend/LICENSE](backend/LICENSE).
