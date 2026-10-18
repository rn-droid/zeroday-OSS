# ADR-0003: SQLite FTS5 for Lexical Retrieval over Dense Vector Embeddings

## Status
Accepted

## Context
Standard RAG frameworks rely on heavy dense vector embeddings (e.g., PyTorch, sentence-transformers, FAISS, ChromaDB). On consumer hardware, loading a 500MB embedding model alongside the LLM consumes excessive RAM, introduces C++ compilation hurdles on Windows, and produces non-deterministic semantic matches that can hallucinate clauses.

## Decision
We chose **SQLite FTS5 full-text search with BM25 ranking** as the primary retrieval engine in Tier 0.

## Consequences
- **Zero Heavy Dependencies:** Uses Python's standard `sqlite3` library with the built-in FTS5 extension.
- **Exact Verbatim Retrieval:** Legal contract queries (e.g., "notice period", "security deposit", "lock-in") rely heavily on exact domain terms, which BM25 captures with precision.
- **Instant Latency:** Retrieval queries execute in under 10 ms on consumer CPUs without GPU acceleration.
