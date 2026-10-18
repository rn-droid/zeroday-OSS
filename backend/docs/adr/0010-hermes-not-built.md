# ADR-0010: Intentional Omission of the Hermes Agentic Framework in Tier 0

## Status
Accepted

## Context
The Solution Guide discussed potential integration of multi-turn autonomous agentic frameworks (e.g., Hermes / LangChain Agent / AutoGPT-style tool looping). While agent loops provide flexible multi-step reasoning, they introduce severe risks for a high-integrity legal document tool:
- **Infinite Loops & Tool Exhaustion:** Models can trigger unbounded retrieval loops.
- **Latency & Resource Spikes:** Each turn consumes seconds of compute, overwhelming consumer hardware.
- **Hallucinatory Drift:** Autonomous agents frequently drift from source documents and fabricate intermediary evidence.

## Decision
We decided **NOT to build or integrate Hermes** in Tier 0 (Survival Mode):
1. Replaced with the deterministic `BoundedRuntime` state machine (`RECEIVE -> CLASSIFY -> PLAN -> RETRIEVE -> ANALYZE -> VALIDATE -> RESPOND`).
2. Maximum tool calls are hard-capped at 8.
3. Maximum LLM inference calls are hard-capped at 4 (with fast-path executing in exactly 1 call or 0 calls).
4. Sentence IDs (`sid`) and quotes must be grounded strictly in SQLite FTS5 outputs.

## Consequences
- **Rock-Solid Predictability:** Guarantees sub-second deterministic execution on lexical fast-paths.
- **Zero Hallucination of Storage or DBs:** The model cannot invent databases, open arbitrary files, or forge sentence IDs.
