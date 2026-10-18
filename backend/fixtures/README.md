# fixtures/README.md — Synthetic fixture provenance

All fixtures in this directory are **synthetic** (own work or CC0).
No real rental agreements, private documents or personal data are committed here.

| File | Type | Target tests | Authors | Licence | Known limitations |
|------|------|-------------|---------|---------|-------------------|
| `synthetic_rental_simple.txt` | Plain TXT | T-ING-*, basic retrieval, silence | Project team | CC0 | No conflicts, no ambiguity |
| `open_india_law_subset_judgment.txt` | Plain TXT | Stress, FTS5 judicial terms, long reasoning | Open India Law (vaquill/open-india-law) | Public Domain / CC-BY | Judicial judgment, not a contract |

## Adding a fixture

Every fixture must be added to this table with:
- File name
- Type (TXT / PDF synthetic)
- Target test IDs
- Author (must be "Project team" or "own work")
- Licence (CC0 or Apache-2.0)
- Known limitations

**Never commit a real agreement, court document or private file.**
**Never commit any file that contains real names, addresses or personal data.**
