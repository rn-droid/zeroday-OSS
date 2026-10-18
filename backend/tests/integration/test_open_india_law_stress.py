"""Integration and stress tests using Open India Law (vaquill/open-india-law) landmark judgment fixture."""
from pathlib import Path
import pytest
import sqlite3

from backend.app.ingest.worker import ingest_document
from backend.app.agent.runtime import BoundedRuntime
from backend.app.agent.tools import DocumentTools
from backend.app.store.db import open_doc_db
from backend.app.config import get_settings


@pytest.mark.asyncio
async def test_open_india_law_judgment_ingestion_and_retrieval(tmp_path: Path):
    """
    Stress-test the ingestion pipeline and FTS5 search on an authentic Indian legal judgment
    from Open India Law (Associated Hotels of India Ltd. v. R.N. Kapoor, AIR 1959 SC 1262).
    """
    repo_root = Path(__file__).resolve().parents[2]
    fixture_path = repo_root / "fixtures" / "open_india_law_subset_judgment.txt"
    assert fixture_path.exists(), f"Fixture missing: {fixture_path}"

    raw_bytes = fixture_path.read_bytes()
    assert len(raw_bytes) > 500

    # 1. Ingest Open India Law judgment
    result = await ingest_document(raw_bytes, "open_india_law_subset_judgment.txt")

    assert result.status == "ready"
    assert result.page_count >= 1
    assert result.quality["sentence_count"] > 10
    doc_id = result.document_id

    # 2. Verify per-document SQLite and FTS5 index
    settings = get_settings()
    db_file = settings.data_dir / doc_id / "doc.sqlite3"
    assert db_file.exists(), f"Database not found at {db_file}"

    con = open_doc_db(db_file)
    tools = DocumentTools(con)

    # 3. Test FTS5 search on complex Indian judicial terminology
    hits_possession = tools.search_document("exclusive possession")
    assert len(hits_possession) > 0
    assert any("exclusive possession" in h["sentence_text"].lower() for h in hits_possession)

    hits_statutes = tools.search_document("Section 105 Section 52 Transfer of Property Easements")
    assert len(hits_statutes) > 0
    assert any("105" in h["sentence_text"] or "52" in h["sentence_text"] for h in hits_statutes)

    hits_fee = tools.search_document("monthly sum licence fee 800")
    assert len(hits_fee) > 0
    assert any("800" in h["sentence_text"] for h in hits_fee)

    # 4. Test BoundedRuntime state machine on judgment text
    runtime = BoundedRuntime(con=con)
    ans = runtime.run("What are the principles to distinguish a lease from a licence?")

    assert ans.status in ("ANSWERED", "LEGAL_LIMIT")
    assert ans.legal_verdict is None  # Permanent invariant
    assert len(ans.claims) > 0 or len(ans.general_explanations) > 0 or len(ans.answer) > 0

    con.close()
