# ADR-0009: Attention-First Priority Ordering for Agreement Review

## Status
Accepted

## Context
Standard contract summary tools list clauses chronologically (Clause 1 to Clause 20) or alphabetically. Non-lawyers reviewing a rental agreement often get fatigued reading standard recitals and boilerplate terms, missing critical risks such as conflicting termination notices, excessive late-payment penalties, or restrictive lock-in periods buried on page 4.

## Decision
We implemented **attention-first priority ordering** in `backend/app/retrieval/review.py`:
The Core 10 rental review topics are sorted into an attention hierarchy:
1. **Clause Conflicts:** Situations where two clauses contradict each other (e.g., 30-day notice vs. 60-day notice) are placed at the very top with dual verbatim citations.
2. **Ambiguities & Non-Standard Clauses:** Unusual penalties, vague maintenance allocations, or restrictive lock-ins.
3. **Core Monetary & Term Obligations:** Rent, security deposit, and tenancy duration.
4. **Disputes & Jurisdiction:** Court venues and arbitration provisions.
5. **Standard Located Clauses:** Standard provisions matching expected patterns.
6. **Not Located:** Categories not found in the agreement.
7. **Not Assessed:** Pages with language or readability flags.

## Consequences
- **User Focus:** Non-lawyers are immediately directed to potential red flags before proceeding to routine terms.
- **Side-by-Side Dual Citations:** Conflicts are clearly displayed side-by-side with physical page numbers so users can cross-examine the text.
