# Reference Datasets Documentation

This document records the provenance, purpose, integration, and caveats for the three optional reference datasets suggested in the ZeroDay OSS Hacktoberfest 2026 Participant Guide for Problem Statement 2 (PS2).

> **Important Notice from the Participant Guide:**  
> These datasets are suggestions, not requirements. Dataset licences, attribution, privacy, access restrictions, and redistribution rights must be checked before use. Contracts, legislation, and court judgments are different types of legal material and must **not** be treated as interchangeable.

---

## 1. Contract Understanding Atticus Dataset (CUAD)

- **Dataset Name:** Contract Understanding Atticus Dataset (CUAD)
- **Official Repository:** [https://github.com/The-Atticus-Project/cuad](https://github.com/The-Atticus-Project/cuad)
- **Licence:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Guide's Description:** 510 commercial contracts, 13,000+ expert labels, and 41 clause types.
- **Intended Purpose (per Guide):** Test contract clause identification against expert-labelled annotations.
- **Caveat (per Guide):** These commercial contracts may differ from rental agreements, so results must not be treated as proof of performance on rental documents.

### How it is integrated in LexiGuard:
1. **Extractive QA Evaluation Suite (`tests/evaluation/`):**
   - Implemented in `tests/evaluation/evaluate_core.py` and configured in `tests/evaluation/ground_truth_questions.json`.
   - Maps CUAD clause categories (Parties, Governing Law, Notice Period to Terminate, Security Deposit/Payment Obligations, Agreement Term, Subletting Restrictions, Inspection/Audit Rights) into deterministic evaluation queries.
   - Computes verbatim span coverage, prompt and completion token counts, latency, and status breakdowns.
   - Outputs structured benchmark results to `docs/reports/eval_results.json`.
2. **Automated Verification:**
   - Hooked into `pytest tests/evaluation/test_evaluation.py`.

---

## 2. India Code

- **Dataset Name:** India Code
- **Official Portal:** [https://indiacode.gov.in](https://indiacode.gov.in/)
- **Intended Purpose (per Guide):** Provide statutory context and support section-level citation tests using Indian legislation.
- **Caveat (per Guide):** Legislation is not a contract. The guide notes that the site's terms have not been verified, so check them before bulk use or redistribution.

### How it is integrated in LexiGuard:
1. **Curated Statutory Context Lexicon (`backend/lexicons/statutory_context.yaml`):**
   - Contains statutory provisions governing tenancy, lease, and licence under Indian law:
     - **Transfer of Property Act, 1882:** Section 105 (Lease defined), Section 106 (Statutory 15-day notice default in absence of contract), Section 107 (Compulsory registration for terms exceeding 1 year), Section 108 (Rights & liabilities), Section 111 (Determination of lease).
     - **Indian Easements Act, 1882:** Section 52 (Licence defined; personal permission without creating an interest in property), Section 60 (Revocation of licence).
     - **Registration Act, 1908:** Section 17(1)(d) (Compulsory registration of leases exceeding 1 year).
     - **Model Tenancy Act, 2021:** Section 10 (Security deposit cap: max 2 months for residential premises), Section 21 (Repossession grounds).
2. **Runtime Section-Level Citations (`backend/app/agent/runtime.py`):**
   - When a user asks about statutory defaults or legal enforceability (triggering `Route.EXTERNAL_LAW_REQUIRED` or `Route.LEGAL_CONCLUSION`), LexiGuard retrieves the matching section from `statutory_context.yaml` and includes the statutory citation in the summary answer.
   - Attaches the mandatory disclaimer:
     > *"Statutory citations derived from India Code (indiacode.gov.in). Legislation is not a contract. Statutory rights and rent control vary by state. Please consult a qualified legal professional."*
   - Injects statutory references into Gemma's prompt as domain context so the model understands the legal framework without hallucinating contract terms.
3. **Automated Verification:**
   - Unit tests in `tests/unit/test_statutory_citations.py` verify section-level citations (e.g., Section 106, Section 52, Section 17) and confirm that `external_law_required` and `recommend_professional_review` are set.

---

## 3. Open India Law

- **Dataset Name:** Open India Law
- **Official Repository:** [https://huggingface.co/datasets/vaquill/open-india-law](https://huggingface.co/datasets/vaquill/open-india-law)
- **Guide's Description:** Includes court judgments, legislation and tribunal matters.
- **Intended Purpose (per Guide):** Support testing with long, complex legal documents and statutory retrieval.
- **Caveat (per Guide):** It is a large dataset; the guide recommends using only a subset. It is a point-in-time snapshot, not a guarantee of current law or legal advice.

### How it is integrated in LexiGuard:
1. **Curated Landmark Judgment Fixture (`fixtures/open_india_law_subset_judgment.txt`):**
   - Uses an authentic subset of the landmark Indian Supreme Court judgment on tenancy/leave-and-licence: *Associated Hotels of India Ltd. v. R.N. Kapoor (AIR 1959 SC 1262)*.
   - Contains the established four-fold legal test distinguishing a Lease (Transfer of Property Act §105) from a Licence (Easements Act §52) based on exclusive possession and intention.
2. **Stress & Retrieval Test Suite (`tests/integration/test_open_india_law_stress.py`):**
   - **Ingestion stress-testing:** Tests that the isolated child-process parser handles real multi-page Indian court judgment formatting without timeouts or memory spikes.
   - **Complex terminology search:** Validates SQLite FTS5 search on dense Indian legal concepts (*"exclusive possession"*, *"test of intention"*, *"licence fee"*, *"Section 52"*).
   - **Contract vs. Judgment boundary:** Confirms that when court documents are processed, the system extracts factual citations while permanently preserving `legal_verdict = None`.

---

## Summary of Dataset Roles in LexiGuard

| Dataset | Type of Legal Material | Project Role | Code Location |
| :--- | :--- | :--- | :--- |
| **CUAD** | Commercial Contracts | Clause extraction benchmark & evaluation | `tests/evaluation/evaluate_core.py`, `ground_truth_questions.json` |
| **India Code** | Central & State Legislation | Statutory context, default rules & section-level citations | `lexicons/statutory_context.yaml`, `backend/app/agent/runtime.py`, `tests/unit/test_statutory_citations.py` |
| **Open India Law** | Court Judgments & Tribunals | Stress-testing long documents & complex Indian legal search | `fixtures/open_india_law_subset_judgment.txt`, `tests/integration/test_open_india_law_stress.py` |
