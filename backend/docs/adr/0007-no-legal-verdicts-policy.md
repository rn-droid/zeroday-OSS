# ADR-0007: Strict Policy Prohibiting Legal Verdicts & Judicial Predictions

## Status
Accepted

## Context
Non-lawyers querying AI about contracts frequently ask questions like "Is this penalty clause legally valid?", "Can my landlord evict me?", or "Is this contract illegal?". AI models often hallucinate legal certainty, potentially causing severe harm to users facing tenancy disputes.

## Decision
We implemented a **fail-closed legal policy engine** in `backend/app/validation/legal_policy.py`:
1. The schema property `legal_verdict` is permanently locked to `null`.
2. Any question inquiring about legal enforceability, statutory validity, or judicial outcomes is intercepted by the router (`Route.LEGAL_CONCLUSION`).
3. The system returns status `LEGAL_LIMIT` with statutory context from India Code (e.g., Transfer of Property Act 1882) and sets `recommend_professional_review: true`.
4. If a language model attempts to output an opinion on contract validity, the post-generation validator nullifies the verdict.

## Consequences
- **Safety & Compliance:** Prevents the system from practicing unauthorized legal advice. Users receive clear, neutral factual extractions and relevant statutory sections to discuss with a lawyer.
