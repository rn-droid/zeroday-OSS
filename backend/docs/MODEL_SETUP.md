# LexiGuard — Model Setup & Verification Guide

This guide provides instructions for downloading, verifying, and running the local Gemma 4 models with Ollama for LexiGuard.

---

## 1. Prerequisites

1. **Ollama Installation:**
   - Download and install Ollama (version ≥ 0.21.1) from [https://ollama.com](https://ollama.com).
   - Verify installation:
     ```bash
     ollama --version
     ```

2. **Hardware Requirements:**
   - **RAM:** Minimum 8 GB (16 GB recommended).
   - **Disk Space:** Approximately 5 GB for model weights.
   - **Operating System:** Windows 10/11, macOS (Apple Silicon or Intel), or Linux x86_64.

---

## 2. Pulling the Pinned Models

Open your terminal and run:

```bash
# Pull primary model (Gemma 4 4B Instruct Quantized)
ollama pull gemma4:e4b-it-q4_K_M

# Pull lightweight fallback model (Gemma 4 2B Instruct Quantized)
ollama pull gemma4:e2b-it-q4_K_M
```

---

## 3. Verifying Model Availability

To verify that the model is recognized by Ollama:

```bash
ollama list
```

You should see an entry for `gemma4:e4b-it-q4_K_M`.

Run a test query directly against the Ollama native API:

```bash
curl http://127.0.0.1:11434/api/tags
```

---

## 4. Starting the Ollama Service

Make sure the Ollama background daemon is running before starting LexiGuard:

- **macOS / Windows:** Ensure the Ollama tray application is running.
- **Linux:**
  ```bash
  systemctl status ollama || ollama serve
  ```

---

## 5. Running LexiGuard with Local Model

When Ollama is running, LexiGuard connects via `http://127.0.0.1:11434` automatically:

```bash
cd backend
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

> **Note on Model-Free Fast-Path:**  
> If Ollama is not running, LexiGuard does not crash. Tier 0 includes a fully deterministic lexical fast-path that extracts answers directly using SQLite FTS5 and the rental topics lexicon.
