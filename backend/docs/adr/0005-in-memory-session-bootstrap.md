# ADR-0005: One-Time URL Fragment Launch Code & In-Memory Bearer Token

## Status
Accepted

## Context
When running an application with a local web UI, other applications or browser tabs on the user's machine could potentially query `http://127.0.0.1:8000` and access sensitive rental documents. We needed a lightweight, zero-configuration authentication mechanism that requires no user passwords or persistent secrets.

## Decision
We implemented a **one-time URL fragment bootstrap** (`#k=<launch_code>`) exchanged for an in-memory Bearer token:
1. Backend generates a 32-byte hex launch code with a 120-second TTL on startup and displays `http://127.0.0.1:8000/#k=<launch_code>`.
2. The URL fragment is never transmitted in HTTP request headers or web server logs.
3. The frontend reads `#k=...` immediately on mount, wipes it from the browser address bar via `history.replaceState`, and exchanges it via `POST /api/session`.
4. The token is stored strictly in JavaScript runtime memory (`useRef`).

## Consequences
- **Privacy & Security:** Closing the browser tab or reloading immediately purges the token. Malicious local processes cannot guess the token or read it from browser storage.
