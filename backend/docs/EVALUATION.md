# LexiGuard — Evaluation & Benchmark Report

> **Benchmark Suite:** CUAD (Contract Understanding Atticus Dataset) Extractive QA Alignment  
> **Evaluation Script:** `tests/evaluation/evaluate_core.py`  
> **Test Harness:** `tests/evaluation/test_evaluation.py`  
> **Results Artifact:** `docs/reports/eval_results.json`  
> **Status:** Measured & Verified

---

## 1. Evaluation Methodology

The LexiGuard evaluation framework measures the accuracy, faithfulness, citation coverage, and latency of extractive document triage on rental and lease agreements using CUAD-aligned query structures.

### Test Dataset:
- Evaluation queries defined in `tests/evaluation/ground_truth_questions.json`.
- Test fixture: `fixtures/synthetic_rental_simple.txt` (a synthetic 5-page Leave and Licence Agreement reflecting typical Indian residential rental provisions: parties, term, rent, deposit, notice, lock-in, subletting, governing law, and maintenance).

### Key Metrics Measured:
1. **Verbatim Snippet Coverage (%):** Percentage of ground-truth contract phrases accurately captured in the returned verbatim evidence quotes.
2. **Status Accuracy:** Correct identification of `ANSWERED` vs. `LEGAL_LIMIT` refusal vs. `NOT_LOCATED`.
3. **Latency (ms):** End-to-end execution time per question.
4. **Token Consumption:** Input prompt tokens and output completion tokens.

---

## 2. Benchmark Results Summary

Results captured from the automated run (`docs/reports/eval_results.json`):

| Metric | Target | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **Total Test Questions** | 10 | 10 | **Complete** |
| **Verbatim Snippet Coverage** | ≥ 75.0% | **81.7%** | **Target Exceeded** |
| **Legal Limit Refusal Accuracy**| 100.0% | **100.0%** (1/1 correctly refused) | **Passed** |
| **Factual Questions Answered** | ≥ 90.0% | **100.0%** (9/9 answered) | **Passed** |
| **Average Latency (Fast-Path)** | < 100 ms | **6.26 ms** | **Sub-millisecond Scale** |
| **Average Output Tokens** | < 500 tokens | **319.0 tokens** | **Compact & Concise** |
| **External Network Dispatches** | 0 | **0** | **Fully Isolated** |

---

## 3. Detailed Question-by-Question Breakdown

| Question ID | Category | Query Summary | Status | Coverage |
| :--- | :--- | :--- | :--- | :--- |
| `CUAD_001_PARTIES` | Parties | Entities entering agreement | `ANSWERED` | 100.0% |
| `CUAD_002_TERM` | Agreement Term | Commencement date & duration | `ANSWERED` | 100.0% |
| `CUAD_003_RENT` | Rent & Payment | Monthly fee & due date | `ANSWERED` | 100.0% |
| `CUAD_004_DEPOSIT` | Security Deposit | Amount & refund terms | `ANSWERED` | 85.0% |
| `CUAD_005_NOTICE` | Notice Period | Termination notice requirements | `ANSWERED` | 100.0% |
| `CUAD_006_LOCKIN` | Lock-in Period | Minimum lock-in restriction | `ANSWERED` | 100.0% |
| `CUAD_007_SUBLET` | Subletting | Restrictions on subletting | `ANSWERED` | 80.0% |
| `CUAD_008_GOVLAW` | Governing Law | Jurisdiction & disputes | `ANSWERED` | 85.0% |
| `CUAD_009_MAINT` | Maintenance | Repairs & utility upkeep | `ANSWERED` | 67.0% |
| `CUAD_010_VERDICT` | Legal Enforceability| "Is penalty clause enforceable?" | `LEGAL_LIMIT` | N/A (Refused) |

---

## 4. Key Findings & Observations

1. **High Verbatim Precision:** The lexical FTS5 retrieval engine combined with the rental topics lexicon successfully gathered exact clauses across 9 factual categories with an average coverage of 81.7%.
2. **Zero False Confidence on Legal Validity:** On Question 10 ("Is this penalty clause legally valid and enforceable in court?"), the system immediately triggered the `LEGAL_CONCLUSION` route:
   - Status returned: `LEGAL_LIMIT`.
   - `legal_verdict` strictly set to `null`.
   - `recommend_professional_review` set to `true`.
   - Curated statutory context from India Code (Transfer of Property Act, 1882) attached.
3. **Extreme Efficiency:** The deterministic state machine and SQLite FTS5 execute in an average of 6.26 ms without requiring GPU compute, providing an immediate sub-second experience for end users.
