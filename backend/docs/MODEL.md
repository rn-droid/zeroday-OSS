# LexiGuard — Language Model Architecture & Specification

> **Pinned Model Family:** Google Gemma 4  
> **Pinned Model Tag:** `gemma4:e4b-it-q4_K_M` (Primary), `gemma4:e2b-it-q4_K_M` (Resource-Constrained Fallback)  
> **Serving Engine:** Ollama Native REST API (`http://127.0.0.1:11434`)  
> **Deterministic Runtime:** Strict single-turn proposing role with post-generation claim validation.

---

## 1. Model Selection & Rationale

LexiGuard selects **Gemma 4** (`gemma4:e4b-it-q4_K_M`) for local, on-device legal document triage based on the following criteria:

1. **Local Efficiency & Footprint:**
   - 4-bit quantized GGUF format (`q4_K_M`) requires under 4.5 GB of RAM/VRAM.
   - Operates comfortably on modern consumer laptops (Apple Silicon, Intel Core i5/i7/i9, AMD Ryzen) without dedicated enterprise GPUs.
2. **Instruction Following & Structured JSON:**
   - Demonstrates strong adherence to system prompts and structured output schemas (`format: "json"`).
   - Capable of distinguishing direct contract facts from interpretations, ambiguities, and concerns.
3. **Licensing & Redistribution:**
   - Distributed under the permissive Gemma Terms of Use, enabling royalty-free local execution and commercial/academic deployment.

---

## 2. Model Operational Configuration

| Parameter | Value | Rationale |
| :--- | :--- | :--- |
| **Model** | `gemma4:e4b-it-q4_K_M` | Balances semantic reasoning with low memory usage. |
| **Temperature** | `0.0` | Maximum determinism, eliminating creative extrapolation. |
| **Top-P** | `0.1` | Narrow nucleus sampling to preserve high-probability tokens. |
| **Context Window (`num_ctx`)**| `8192` | Sufficient for retrieved top-k candidate sentences + query. |
| **Max Output Tokens (`num_predict`)** | `1024` | Ample headroom for structured claims and citations. |
| **Output Format** | `json` | Enforces JSON output from Ollama native endpoint. |

---

## 3. Role of the Model in the System

In LexiGuard, **the model proposes; deterministic code decides**:

```
[User Query + Retrieved Sentences]
              │
              ▼
    [Local Gemma 4 Model]
              │
              ▼
   [Raw Proposed JSON Answer]
              │
              ▼
  [Deterministic Validators]
  - Literal Number Validator (checks Rs. amounts & dates against quotes)
  - Provenance Validator (discards fabricated sentence IDs)
  - Legal Policy Validator (nullifies legal_verdict & adds disclaimers)
              │
              ▼
    [Verified RenderedAnswer]
```

1. **No Judicial Prediction:** The model is strictly instructed via system prompt never to declare whether a clause or contract is legally binding, fair, or enforceable. If the model attempts to emit a legal verdict, the `legal_policy.py` validator overrides it to `null`.
2. **Immutable Verbatim Quoting:** The model must extract quotes verbatim from provided sentences. Any claim that references non-existent numbers or dates is downgraded or rejected by `literal.py`.
3. **No Unconstrained Loops:** In Tier 0, the model is invoked at most once per user question, with an absolute hard ceiling of 4 calls if JSON format parsing fails.

---

## 4. Prompt Engineering & System Instructions

The prompt templates are defined in `backend/app/agent/runtime.py`:

```
SYSTEM PROMPT:
You are LexiGuard, a private on-device legal document triage assistant for rental agreements.
Your task is to examine ONLY the provided contract sentences and answer the user question.

STRICT RULES:
1. ONLY use facts directly stated in the provided sentences.
2. You MUST cite exact sentence IDs (sid) and verbatim quotes for every claim.
3. You MUST NEVER pronounce on whether the agreement or clause is legally binding, valid, fair, or enforceable.
4. If the provided sentences do not contain the answer, set status to 'NOT_LOCATED' or 'INSUFFICIENT_EVIDENCE'.
5. Always output valid JSON conforming to the schema.
```

---

## 5. Model Failure & Fallback Handling

- **Ollama Unavailable / Not Installed:** If connection to `http://127.0.0.1:11434` fails, the system executes the deterministic fast-path fallback (`lexical.py` + regex fact extractor) or returns `ERROR_LOCAL_MODEL_UNAVAILABLE` with clear instructions to run `ollama serve`.
- **Malformed JSON Output:** If Ollama returns non-JSON or invalid syntax, the runtime retries with a corrective prompt up to 2 times before falling back to lexical extractive summaries.
