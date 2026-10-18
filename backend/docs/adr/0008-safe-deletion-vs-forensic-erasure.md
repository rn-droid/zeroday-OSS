# ADR-0008: Safe Deletion & Truthful Forensic Erasure Caveats

## Status
Accepted

## Context
When a user deletes a sensitive document, privacy-oriented applications frequently claim to "permanently erase" or "shred" data. However, on modern flash storage (SSDs with wear-leveling controllers), operating system swap files, and journaled filesystems, standard file unlinking does not guarantee that raw NAND flash blocks are sanitized.

## Decision
We implemented a **verified two-phase deletion service** accompanied by a **transparent limitation notice**:
1. `backend/app/store/delete.py` closes SQLite connection pools, enables PRAGMA `secure_delete=ON`, unlinks the database file and directory, and verifies that `os.path.exists()` returns `False`.
2. The API response (`DeleteResponse`) explicitly reports:
   - `app_files_removed: true`
   - `fts_rows_removed: true`
   - `directory_absent: true`
   - `note`: *"App-controlled files removed. This does NOT constitute forensic erasure from SSD, OS swap, or external backups. See docs/LIMITATIONS.md."*

## Consequences
- **Truthful Engineering:** Avoids giving users a false sense of cryptographic or forensic security while ensuring that all application-controlled storage is completely purged.
