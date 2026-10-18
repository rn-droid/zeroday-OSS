# ADR-0002: Selection of pypdfium2 over PyMuPDF

## Status
Accepted

## Context
PDF text extraction is the first stage of the ingestion pipeline. PyMuPDF (fitz) is commonly used in Python, but is licensed under GNU AGPLv3. PyPDF2 / pypdf has historic parsing errors with complex layout fonts. `pypdfium2` is a Python binding to Google PDFium.

## Decision
We chose **`pypdfium2`** executed in a separate, isolated child process.

## Consequences
- **License Compliance:** `pypdfium2` is licensed under Apache-2.0 / BSD-3-Clause, making it compatible with LexiGuard's Apache-2.0 open-source licensing without viral copyleft obligations.
- **Sandboxing & Crash Protection:** By executing the parser in a dedicated child process with a 15-second watchdog timer and 10 MB output buffer cap, malformed PDFs or PDFium crashes cannot bring down the main FastAPI application server.
