# ADR-0006: React 19 + TypeScript + Vite with Zero External CDNs

## Status
Accepted

## Context
Many modern frontend templates load fonts from Google Fonts, icons from FontAwesome/Unpkg, and analytics/telemetry scripts from third-party networks. For a privacy-first legal tool, any external network connection leaks metadata or IP addresses.

## Decision
We chose **React 19 + TypeScript + Vite** configured with **strict local-only bundling**:
1. All CSS typography uses system font stacks (`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`).
2. All icons are embedded SVGs or local SVG sprite assets.
3. Zero external script or stylesheet tags in `index.html`.
4. Production bundle is compiled into static files (`dist/`) and mounted directly on FastAPI root `/`.

## Consequences
- **Total Network Isolation:** The browser makes zero outbound requests to external domains, verified by our automated privacy audit suite.
- **Fast Startup:** No render-blocking network font requests or external script loading.
