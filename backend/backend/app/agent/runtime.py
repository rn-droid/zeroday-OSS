"""Bounded runtime state machine for question answering (Guide §8.3).

Flow: RECEIVE -> CLASSIFY -> PLAN -> RETRIEVE -> ANALYZE -> VALIDATE -> RESPOND.
Fast Path: Single Gemma call when lexical retrieval is confident.
Hard limits:
- Max 4 Gemma calls total (including retries)
- Max 8 tool calls total
- Max 2 retrieve loops
- Question <= 500 characters
"""
from __future__ import annotations

import logging
import secrets
import sqlite3
from typing import Any, Dict, List, Optional, Set
from pathlib import Path

from backend.app.agent.router import Route, route_query
from backend.app.agent.schema import ModelAnswer, ModelPoint
from backend.app.agent.tools import DocumentTools
from backend.app.model.provider import LLMProvider
from backend.app.retrieval.silence import STATUS_LOCATED, STATUS_NOT_LOCATED, check_silence
from backend.app.validation.legal_policy import scan_verdict
from backend.app.validation.literal import validate_restatement
from backend.app.validation.provenance import validate_provenance
from backend.app.validation.renderer import RenderedAnswer, render_response

logger = logging.getLogger("lexiguard.agent.runtime")

MAX_GEMMA_CALLS = 4
MAX_TOOL_CALLS = 8
MAX_RETRIEVE_LOOPS = 2


def _load_glossary() -> Dict[str, Dict[str, Any]]:
    """Load curated glossary terms."""
    root = Path(__file__).resolve().parents[3]
    candidate = root / "glossary" / "rental_terms.yaml"
    if not candidate.exists():
        candidate = Path("glossary/rental_terms.yaml")
    if not candidate.exists():
        return {}

    content = candidate.read_text(encoding="utf-8")
    try:
        import yaml
        loaded = yaml.safe_load(content)
        return loaded.get("terms", {}) if isinstance(loaded, dict) else {}
    except Exception:
        pass

    # Simple fallback parser for terms
    terms: Dict[str, Dict[str, Any]] = {}
    current_term = None
    for line in content.splitlines():
        if line.startswith("  ") and line.endswith(":") and not line.strip().startswith("terms:"):
            current_term = line.strip()[:-1]
            terms[current_term] = {}
        elif current_term and "definition:" in line:
            parts = line.split("definition:", 1)
            terms[current_term]["definition"] = parts[1].strip().strip('"')
    return terms


def _load_topics() -> Dict[str, Any]:
    """Load rental topic lexicons."""
    root = Path(__file__).resolve().parents[3]
    candidate = root / "lexicons" / "rental_topics.yaml"
    if not candidate.exists():
        candidate = Path("lexicons/rental_topics.yaml")
    if not candidate.exists():
        return {}
    content = candidate.read_text(encoding="utf-8")
    try:
        import yaml
        loaded = yaml.safe_load(content)
        return loaded.get("topics", {}) if isinstance(loaded, dict) else {}
    except Exception:
        return {}


def _load_statutory_context() -> Dict[str, Any]:
    """Load Indian statutory context from India Code (indiacode.gov.in)."""
    root = Path(__file__).resolve().parents[3]
    candidate = root / "lexicons" / "statutory_context.yaml"
    if not candidate.exists():
        candidate = Path("lexicons/statutory_context.yaml")
    if not candidate.exists():
        return {}
    content = candidate.read_text(encoding="utf-8")
    try:
        import yaml
        loaded = yaml.safe_load(content)
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        return {}


def _match_statutory_sections(question: str, statutory_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Match relevant Indian legislation sections from India Code for a query."""
    q_lower = question.lower()
    matches: List[Dict[str, Any]] = []
    statutes = statutory_data.get("statutes", {})
    for _, stat in statutes.items():
        act_name = stat.get("act_name", "")
        sections = stat.get("sections", {})
        for _, sec in sections.items():
            keywords = sec.get("keywords", [])
            sec_num = sec.get("section_number", "").lower()
            if sec_num in q_lower or any(kw in q_lower for kw in keywords):
                matches.append({
                    "act_name": act_name,
                    "section_number": sec.get("section_number", ""),
                    "heading": sec.get("heading", ""),
                    "statutory_summary": sec.get("statutory_summary", ""),
                })
    return matches


def _build_reference_context(
    question: str,
    glossary: Dict[str, Dict[str, Any]],
    topics: Dict[str, Any],
    statutory_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build a compact reference block from glossary, topic keywords, and statutory
    context from India Code relevant to the question. Injected into Gemma's prompt.
    """
    q_lower = question.lower()
    lines: List[str] = []

    # Match glossary terms mentioned in the question
    matched_terms = [
        (term, entry)
        for term, entry in glossary.items()
        if term in q_lower or any(w in q_lower for w in term.split())
    ]
    if matched_terms:
        lines.append("## Glossary Reference")
        for term, entry in matched_terms:
            defn = entry.get("definition", "")
            note = entry.get("note", "")
            lines.append(f"- **{entry.get('term', term)}**: {defn}")
            if note:
                lines.append(f"  *(Note: {note})*")

    # Match topic synonyms mentioned in the question
    matched_topics = [
        (key, data)
        for key, data in topics.items()
        if any(syn in q_lower for syn in data.get("synonyms", []))
    ]
    if matched_topics:
        lines.append("## Relevant Topics")
        for key, data in matched_topics:
            syns = ", ".join(data.get("synonyms", [])[:6])
            lines.append(f"- **{data.get('label', key)}** (keywords: {syns})")

    # Match Indian statutory provisions from India Code
    if statutory_data:
        stat_matches = _match_statutory_sections(question, statutory_data)
        if stat_matches:
            lines.append("## Statutory Reference (India Code — indiacode.gov.in)")
            lines.append("*(Note: Legislation is not a contract. Statutory defaults apply only where agreement is silent or governed by mandatory law.)*")
            for sm in stat_matches[:2]:
                lines.append(f"- **{sm['act_name']}, {sm['section_number']} ({sm['heading']})**: {sm['statutory_summary']}")

    return "\n".join(lines)


def _get_full_document_text(con: sqlite3.Connection, max_chars: int = 80_000) -> str:
    """
    Fetch all page text from the SQLite store, ordered by page number.
    Caps at max_chars to stay within Gemma's context window.
    """
    rows = con.execute(
        "SELECT page_num, norm_text FROM pages WHERE is_readable = 1 AND lang_supported = 1 ORDER BY page_num"
    ).fetchall()
    parts: List[str] = []
    total = 0
    for row in rows:
        page_text = f"[Page {row['page_num']}]\n{row['norm_text']}"
        if total + len(page_text) > max_chars:
            parts.append("[...document truncated for context window...]")
            break
        parts.append(page_text)
        total += len(page_text)
    return "\n\n".join(parts)


class BoundedRuntime:
    """State machine governing bounded question answering over a document."""

    def __init__(
        self,
        con: sqlite3.Connection,
        provider: Optional[LLMProvider] = None,
    ) -> None:
        self.con = con
        self.provider = provider
        self.tools = DocumentTools(con)
        self.gemma_calls = 0
        self.tool_calls = 0
        self.retrieve_loops = 0
        self.approved_sids: Set[str] = set()

    def run(self, question: str) -> RenderedAnswer:
        """Execute bounded state machine."""
        # 1. RECEIVE & CLASSIFY
        decision = route_query(question)

        # 2. PLAN & DISPATCH
        if decision.route == Route.OUT_OF_SCOPE:
            return render_response(
                con=self.con,
                status="OUT_OF_SCOPE",
                summary_answer=decision.reason,
                points=[],
            )

        if decision.route == Route.DOCUMENT_MAP:
            if self.tool_calls < MAX_TOOL_CALLS:
                self.tool_calls += 1
                sections = self.tools.get_document_map()
                summary = "Here is the structure of the document sections:\n" + "\n".join(
                    f"- {s['section']} (Page {s['start_page']})" for s in sections
                )
                return render_response(
                    con=self.con,
                    status="ANSWERED",
                    summary_answer=summary,
                    points=[],
                )

        if decision.route == Route.DOCUMENT_SUMMARY:
            # 1. Gather key provisions across agreement: recitals (page 1) + core topics
            recital_rows = self.con.execute(
                """
                SELECT sid, page_num, section, sentence_text
                FROM sentences
                WHERE page_num = 1
                ORDER BY start_offset
                LIMIT 5
                """
            ).fetchall()

            summary_hits: List[Dict[str, Any]] = [
                {
                    "sid": r["sid"],
                    "page_num": r["page_num"],
                    "section": r["section"],
                    "sentence_text": r["sentence_text"],
                }
                for r in recital_rows
            ]

            # Query core topics: term, rent, deposit, notice, restrictions, disputes
            core_topics = ["term", "rent", "deposit", "notice", "restrictions", "disputes"]
            for top in core_topics:
                if self.tool_calls < MAX_TOOL_CALLS:
                    self.tool_calls += 1
                    top_hits = self.tools.search_document(query="", topic=top)
                    for th in top_hits[:2]:
                        if not any(sh["sid"] == th["sid"] for sh in summary_hits):
                            summary_hits.append(th)

            # Record approved sids
            for sh in summary_hits:
                self.approved_sids.add(sh["sid"])

            # 2. If provider is available, use Gemma to synthesize an intelligent, structured summary
            if self.provider and self.gemma_calls < MAX_GEMMA_CALLS:
                nonce = secrets.token_hex(6)
                evidence_lines = [
                    f"[{h['sid']}] (Section: {h['section']}, Page: {h['page_num']}) {h['sentence_text']}"
                    for h in summary_hits
                ]
                evidence_block = (
                    f"<<EVIDENCE-{nonce}>>\n"
                    + "\n".join(evidence_lines)
                    + f"\n<<END-EVIDENCE-{nonce}>>"
                )
                full_doc_text = _get_full_document_text(self.con)
                topics = _load_topics()
                glossary = _load_glossary()
                ref_context = _build_reference_context(question, glossary, topics)

                system_prompt = (
                    "You are LexiGuard, a private legal-document triage assistant.\n"
                    "The user is asking for a comprehensive summary of this agreement.\n"
                    "Carefully examine the full agreement text and the retrieved evidence passages.\n\n"
                    "Rules for Summary:\n"
                    "1. Propose clear, accurate points summarizing key aspects of the agreement:\n"
                    "   - Agreement type, date, and Parties (Licensor / Landlord and Licensee / Tenant)\n"
                    "   - Premises / Property description and location\n"
                    "   - Term & Duration (commencement and expiry dates)\n"
                    "   - Financial terms (Monthly rent/fee, due dates, payment mode)\n"
                    "   - Security Deposit amount, refund timeline, and deduction conditions\n"
                    "   - Termination rules (notice period days, lock-in period)\n"
                    "   - Major restrictions (subletting, alterations, pet policies)\n"
                    "   - Dispute resolution mechanism and governing jurisdiction\n"
                    "2. Set kind to 'STATED' or 'RESTATEMENT'.\n"
                    "3. Set sids to the exact sentence IDs from the evidence block supporting each point.\n"
                    "4. NEVER invent dates, numbers, or amounts. Everything must be grounded in the text.\n"
                    "5. DO NOT provide legal advice or legal enforceability judgments.\n"
                )
                if ref_context:
                    system_prompt += f"\n## Reference Context (terminology guide)\n{ref_context}\n"

                user_prompt = (
                    f"Question: Please provide a clear, comprehensive summary of this agreement.\n\n"
                    f"Retrieved Key Provisions:\n{evidence_block}\n\n"
                    f"Full Agreement Text:\n{full_doc_text}"
                )

                self.gemma_calls += 1
                try:
                    model_answer: ModelAnswer = self.provider.generate_structured(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        response_schema=ModelAnswer,
                    )
                except Exception as exc:
                    logger.warning("Local LLM provider error (%s); falling back to extractive summary.", exc)
                    model_answer = ModelAnswer(points=[])

                valid_points, _ = validate_provenance(model_answer, self.approved_sids)
                verified_points: List[ModelPoint] = []
                for pt in valid_points:
                    source_texts = []
                    for sid in pt.sids:
                        row = self.con.execute("SELECT sentence_text FROM sentences WHERE sid = ?", (sid,)).fetchone()
                        if row:
                            source_texts.append(row["sentence_text"])
                    if pt.kind.upper() == "RESTATEMENT":
                        ok_lit, _ = validate_restatement(pt, source_texts)
                        if not ok_lit:
                            continue
                    ok_scan, _ = scan_verdict(pt.text, kind=pt.kind, cited_sources=source_texts)
                    if not ok_scan:
                        continue
                    verified_points.append(pt)

                if verified_points:
                    summary_text = (
                        "Executive Summary: This agreement establishes a residential tenancy / leave-and-licence "
                        "between the parties. Key terms including parties, premises, term duration, monthly rent, "
                        "security deposit, termination notice, and dispute resolution are detailed below with source citations."
                    )
                    return render_response(
                        con=self.con,
                        status="ANSWERED",
                        summary_answer=summary_text,
                        points=verified_points,
                    )

            # Extractive fallback if model provider is omitted or failed
            points = [
                ModelPoint(
                    point_id=f"p_{i}",
                    kind="STATED",
                    text=h["sentence_text"],
                    sids=[h["sid"]],
                )
                for i, h in enumerate(summary_hits[:8])
            ]
            summary_text = (
                "Executive Summary: Key provisions extracted across parties, term, rent, security deposit, "
                "notice period, and dispute resolution are presented below with verbatim citations."
            )
            return render_response(
                con=self.con,
                status="ANSWERED",
                summary_answer=summary_text,
                points=points,
            )

        if decision.route == Route.DOCUMENT_SILENCE_CHECK:
            topic = decision.target_topic or question
            if self.tool_calls < MAX_TOOL_CALLS:
                self.tool_calls += 1
                silence_res = self.tools.check_document_silence(topic)
                points: List[ModelPoint] = []
                for idx, h in enumerate(silence_res["hits"]):
                    points.append(
                        ModelPoint(
                            point_id=f"p_{idx}",
                            kind="STATED",
                            text=h["sentence_text"],
                            sids=[h["sid"]],
                        )
                    )
                return render_response(
                    con=self.con,
                    status=silence_res["status"],
                    summary_answer=silence_res["explanation"],
                    points=points,
                )

        if decision.route == Route.TERM_EXPLANATION:
            term = decision.target_topic or question
            glossary = _load_glossary()
            term_clean = term.lower().strip()
            definition_entry = glossary.get(term_clean)

            # Search document for occurrences
            doc_hits = []
            if self.tool_calls < MAX_TOOL_CALLS:
                self.tool_calls += 1
                doc_hits = self.tools.search_document(query=term)

            points = []
            if definition_entry:
                def_text = f"General definition: {definition_entry.get('definition', '')}"
                points.append(
                    ModelPoint(
                        point_id="p_def",
                        kind="GENERAL_EXPLANATION",
                        text=def_text,
                        sids=[],
                    )
                )

            for idx, h in enumerate(doc_hits[:3]):
                points.append(
                    ModelPoint(
                        point_id=f"p_doc_{idx}",
                        kind="STATED",
                        text=h["sentence_text"],
                        sids=[h["sid"]],
                    )
                )

            def_str = definition_entry.get("definition", "No curated glossary entry found.") if definition_entry else "No curated glossary entry found."
            answer = f"Explanation of '{term}':\n{def_str}"
            return render_response(
                con=self.con,
                status="ANSWERED",
                summary_answer=answer,
                points=points,
            )

        # 3. RETRIEVE
        self.retrieve_loops += 1
        self.tool_calls += 1
        hits = self.tools.search_document(query=question, topic=decision.target_topic)

        # Record approved sids
        for h in hits:
            self.approved_sids.add(h["sid"])

        # Check silence gate if zero hits found
        if not hits:
            silence_res = check_silence(self.con, topic=decision.target_topic or question, query=question)
            return render_response(
                con=self.con,
                status=silence_res.status,
                summary_answer=silence_res.explanation,
                points=[],
            )

        # Handle LEGAL_CONCLUSION limitation route:
        # We retrieve the relevant text, but refuse legal verdicts and recommend professional review.
        # Enriched with statutory section citations from India Code (indiacode.gov.in).
        if decision.is_limitation and decision.route in (Route.LEGAL_CONCLUSION, Route.EXTERNAL_LAW_REQUIRED):
            statutory_data = _load_statutory_context()
            stat_matches = _match_statutory_sections(question, statutory_data)

            points = [
                ModelPoint(
                    point_id=f"p_{i}",
                    kind="STATED",
                    text=h["sentence_text"],
                    sids=[h["sid"]],
                )
                for i, h in enumerate(hits[:5])
            ]

            summary_parts = [
                "LexiGuard provides factual document triage and cannot provide legal verdicts, "
                "enforceability determinations, or judicial predictions. Below are the relevant "
                "clauses located in your agreement."
            ]
            if stat_matches:
                summary_parts.append("\n\nRelevant Statutory Provisions (India Code — indiacode.gov.in):")
                for sm in stat_matches[:2]:
                    summary_parts.append(
                        f"\n• {sm['act_name']}, {sm['section_number']} ({sm['heading']}): {sm['statutory_summary']}"
                    )
                summary_parts.append(
                    "\n\nDisclaimer: Statutory citations derived from India Code (indiacode.gov.in). "
                    "Legislation is not a contract. Statutory rights and rent control vary by state. "
                    "Please consult a qualified legal professional."
                )
            else:
                summary_parts.append(
                    " Please consult a qualified legal professional to evaluate enforceability under applicable jurisdiction law."
                )

            return render_response(
                con=self.con,
                status="LEGAL_LIMIT",
                summary_answer="".join(summary_parts),
                points=points,
                external_law_required=True,
                recommend_review=True,
            )

        # 4. ANALYZE (Fast Path: Exactly 1 Gemma Call)
        if not self.provider or self.gemma_calls >= MAX_GEMMA_CALLS:
            # Fallback to direct stated facts when model provider is omitted (e.g. tests or model limit)
            points = [
                ModelPoint(
                    point_id=f"p_{i}",
                    kind="STATED",
                    text=h["sentence_text"],
                    sids=[h["sid"]],
                )
                for i, h in enumerate(hits[:5])
            ]
            return render_response(
                con=self.con,
                status="ANSWERED",
                summary_answer="Extracted relevant agreement provisions.",
                points=points,
            )

        # Build nonce-delimited evidence block from lexical hits
        nonce = secrets.token_hex(6)
        evidence_lines = [
            f"[{h['sid']}] (Section: {h['section']}, Page: {h['page_num']}) {h['sentence_text']}"
            for h in hits
        ]
        evidence_block = (
            f"<<EVIDENCE-{nonce}>>\n"
            + "\n".join(evidence_lines)
            + f"\n<<END-EVIDENCE-{nonce}>>"
        )

        # Load full document text and reference data (Glossary + Topics + India Code Statutory Context)
        full_doc_text = _get_full_document_text(self.con)
        glossary = _load_glossary()
        topics = _load_topics()
        statutory_data = _load_statutory_context()
        ref_context = _build_reference_context(question, glossary, topics, statutory_data)

        system_prompt = (
            "You are LexiGuard, a private legal-document triage assistant.\n"
            "You have been given the FULL TEXT of a rental or leave-and-licence agreement "
            "and a set of retrieved evidence passages most relevant to the user's question.\n"
            "Use the full document text as your primary source of truth. "
            "The evidence passages highlight the most relevant sections.\n\n"
            "Rules:\n"
            "- Extract statements directly grounded in the document text.\n"
            "- Set kind to 'STATED' or 'RESTATEMENT'.\n"
            "- Set sids to the exact sentence IDs from the evidence block supporting each point.\n"
            "- NEVER invent dates, numbers, or amounts.\n"
            "- DO NOT make legal conclusions or evaluate enforceability.\n"
            "- Use the Reference Context below only to understand legal terminology — "
            "do NOT use it to make claims not found in the document.\n"
        )
        if ref_context:
            system_prompt += f"\n## Reference Context (terminology guide)\n{ref_context}\n"

        user_prompt = (
            f"Question: {question}\n\n"
            f"Retrieved Evidence (most relevant passages):\n{evidence_block}\n\n"
            f"Full Agreement Text:\n{full_doc_text}"
        )

        self.gemma_calls += 1
        try:
            model_answer: ModelAnswer = self.provider.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=ModelAnswer,
            )
        except Exception as exc:
            logger.warning("Local LLM provider error (%s); falling back to extractive provisions.", exc)
            model_answer = ModelAnswer(points=[])

        # 5. VALIDATE
        # Provenance check: drop forged/unapproved sids
        valid_points, dropped_reasons = validate_provenance(model_answer, self.approved_sids)

        verified_points: List[ModelPoint] = []
        for pt in valid_points:
            # Fetch source texts for cited sids
            source_texts = []
            for sid in pt.sids:
                row = self.con.execute("SELECT sentence_text FROM sentences WHERE sid = ?", (sid,)).fetchone()
                if row:
                    source_texts.append(row["sentence_text"])

            # Literal validation for restatements
            if pt.kind.upper() == "RESTATEMENT":
                ok_lit, reason = validate_restatement(pt, source_texts)
                if not ok_lit:
                    logger.warning("Dropping restatement point %s: %s", pt.point_id, reason)
                    continue

            # Legal Policy Verdict Scanner
            ok_scan, scan_reason = scan_verdict(pt.text, kind=pt.kind, cited_sources=source_texts)
            if not ok_scan:
                logger.warning("Dropping point %s due to verdict scan: %s", pt.point_id, scan_reason)
                continue

            verified_points.append(pt)

        # 6. RESPOND
        if not verified_points:
            # Fall back to extractive STATED points from top hits
            verified_points = [
                ModelPoint(
                    point_id=f"p_{i}",
                    kind="STATED",
                    text=h["sentence_text"],
                    sids=[h["sid"]],
                )
                for i, h in enumerate(hits[:5])
            ]

        summary_answer = " ".join(pt.text for pt in verified_points[:5])
        return render_response(
            con=self.con,
            status="ANSWERED",
            summary_answer=summary_answer,
            points=verified_points,
        )
