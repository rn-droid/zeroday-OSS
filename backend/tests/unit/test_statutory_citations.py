"""Unit tests for India Code statutory context and section-level citations."""
import sqlite3
from pathlib import Path

from backend.app.agent.runtime import (
    BoundedRuntime,
    _load_statutory_context,
    _match_statutory_sections,
)
from backend.app.agent.schema import ModelAnswer, ModelPoint
from backend.app.store.db import open_doc_db
from backend.app.store.documents import insert_document
from backend.app.store.pages import insert_page
from backend.app.store.sentences import insert_sentences
from backend.app.ingest.segment import segment_page


def test_load_statutory_context_from_india_code():
    """Verify statutory_context.yaml loads valid Indian statutes from India Code."""
    data = _load_statutory_context()
    assert "statutes" in data
    assert "source" in data
    assert "indiacode.gov.in" in data["source"]

    statutes = data["statutes"]
    assert "transfer_of_property_act_1882" in statutes
    assert "indian_easements_act_1882" in statutes
    assert "registration_act_1908" in statutes
    assert "model_tenancy_act_2021" in statutes

    # Verify Section 106 of TPA
    tpa = statutes["transfer_of_property_act_1882"]
    assert "Section 106" in tpa["sections"]["section_106"]["section_number"]
    assert "15 days" in tpa["sections"]["section_106"]["statutory_summary"] or "fifteen days" in tpa["sections"]["section_106"]["statutory_summary"]


def test_match_statutory_sections():
    """Verify matching of statutory queries to specific Indian Acts and sections."""
    data = _load_statutory_context()

    # Query matching TPA Section 106
    matches_106 = _match_statutory_sections("Is there a statutory notice period of 15 days under section 106?", data)
    assert len(matches_106) > 0
    assert any("Section 106" in m["section_number"] for m in matches_106)
    assert any("Transfer of Property Act" in m["act_name"] for m in matches_106)

    # Query matching Easements Act Section 52 (Licence)
    matches_52 = _match_statutory_sections("Does this leave and licence create a tenancy under section 52?", data)
    assert len(matches_52) > 0
    assert any("Section 52" in m["section_number"] for m in matches_52)
    assert any("Indian Easements Act" in m["act_name"] for m in matches_52)

    # Query matching Registration Act Section 17
    matches_reg = _match_statutory_sections("Is compulsory registration required for an agreement exceeding one year under section 17?", data)
    assert len(matches_reg) > 0
    assert any("Section 17" in m["section_number"] for m in matches_reg)


def test_statutory_context_injected_on_legal_limitation(tmp_path: Path):
    """Verify BoundedRuntime surfaces statutory citations and disclaimers on limitation queries."""
    db_path = tmp_path / "test_doc.sqlite3"
    con = open_doc_db(db_path)

    insert_document(con, "doc_stat_test", "fake_hash", "txt", 1, False)
    text = "9.1 Notice period for termination shall be 30 days. Governing law is the laws of India."
    insert_page(con, "doc_stat_test", 1, text, True, True, [])
    sents = segment_page("doc_stat_test", 1, text)
    insert_sentences(con, sents)
    con.commit()

    runtime = BoundedRuntime(con=con)
    # Question asking about legal enforceability / eviction
    answer = runtime.run("Is this termination clause legally valid or enforceable under section 106?")

    assert answer.status == "LEGAL_LIMIT"
    assert answer.external_law_required is True
    assert answer.recommend_professional_review is True
    # Verify statutory citation from India Code is present
    assert "India Code — indiacode.gov.in" in answer.answer
    assert "Section 106" in answer.answer
    assert "Legislation is not a contract" in answer.answer
    con.close()
