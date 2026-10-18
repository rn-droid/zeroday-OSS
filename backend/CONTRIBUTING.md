# Contributing to LexiGuard

Thank you for your interest in contributing to **LexiGuard**!

LexiGuard is an open-source, local-first legal document triage system for rental and leave-and-licence agreements, developed under the Apache-2.0 License.

---

## 1. Guiding Principles for Contributors

- **Absolute Privacy First:** Never introduce dependencies or code that makes outbound network requests or reports telemetry. The application must remain 100% functional offline on `127.0.0.1`.
- **No Mocked or Claim-Only Code:** All features must have corresponding unit and integration tests. Do not submit stubs that claim tests pass without real assertions.
- **Fail Closed & No Legal Advice:** The system must never pronounce on contract legality or enforceability. Always route statutory questions to neutral extractions with legal disclaimers.
- **Permissive Licensing:** Do not introduce AGPL, GPL, or proprietary dependencies. All components must be compatible with Apache-2.0.

---

## 2. Development Setup

```bash
# 1. Clone the repository and enter backend directory
cd backend

# 2. Create and activate a Python 3.11+ virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install backend dependencies in editable development mode
pip install -e ".[dev]"

# 4. Set up the frontend
cd ../frontend
npm install
npm run build
```

---

## 3. Running Tests & Quality Checks

Before submitting a Pull Request, ensure all tests and linters pass:

```bash
# Backend pytest suite (70 tests)
cd backend
pytest

# Backend code formatting & linting
ruff check .

# Frontend test suite (16 tests)
cd ../frontend
npm test

# Frontend linting & build verification
npm run lint
npm run build
```

---

## 4. Synthetic Fixtures Only

**CRITICAL PRIVACY RULE:** Never commit a real rental agreement, personal document, Aadhaar/PAN number, address, or API key to the repository. All test documents must be entirely synthetic and marked as such in accordance with `fixtures/README.md`.
