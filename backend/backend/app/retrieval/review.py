"""Core 10 Rental Review and Risk Assessment Engine (Guide §7.4, Spec §5.3).

Assesses agreement provisions across the Core 10 topics in attention-first priority:
1. Parties
2. Term & Commencement
3. Rent & Charges
4. Security Deposit
5. Notice & Termination
6. Lock-in Period
7. Penalties & Late Fees
8. Restrictions & Prohibitions
9. Maintenance & Repairs
10. Dispute Resolution & Jurisdiction
"""
from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.retrieval.silence import (
    STATUS_LOCATED,
    STATUS_NOT_LOCATED,
    check_silence,
)


class EvidenceItem(BaseModel):
    sid: str
    page: int
    section: str
    quote: str
    ocr_derived: bool = False


class ReviewTopic(BaseModel):
    topic_id: str
    label: str
    status: str  # "FOUND" | "NOT_FOUND" | "AMBIGUOUS" | "POSSIBLE_CONFLICT" | "NOT_ASSESSED"
    evidence: List[EvidenceItem] = Field(default_factory=list)
    attention_reason: Optional[str] = None


class ProfessionalQuestion(BaseModel):
    question_id: str
    text: str
    evidence: List[EvidenceItem] = Field(default_factory=list)


class ReviewResponse(BaseModel):
    topics: List[ReviewTopic]
    professional_questions: List[ProfessionalQuestion]


CORE_10_TOPIC_CONFIG = [
    {
        "id": "parties",
        "label": "1. Parties & Entities",
        "query": "parties licensor licensee landlord tenant",
    },
    {
        "id": "term",
        "label": "2. Agreement Term & Duration",
        "query": "term tenure duration commencement expiry period months",
    },
    {
        "id": "rent",
        "label": "3. Rent & Charges",
        "query": "rent licence fee monthly escalation due date payment",
    },
    {
        "id": "deposit",
        "label": "4. Security Deposit",
        "query": "security deposit advance refund deduction forfeiture",
    },
    {
        "id": "notice",
        "label": "5. Notice & Termination",
        "query": "notice termination vacate terminate end of tenancy written notice",
    },
    {
        "id": "lock_in",
        "label": "6. Lock-in Period",
        "query": "lock-in lock in minimum period cannot terminate mandatory stay",
    },
    {
        "id": "penalties",
        "label": "7. Penalties & Late Fees",
        "query": "penalty penalties late fee interest delayed payment default charges",
    },
    {
        "id": "restrictions",
        "label": "8. Restrictions & Prohibitions",
        "query": "restrictions prohibited shall not sublet subletting pets commercial alteration",
    },
    {
        "id": "maintenance",
        "label": "9. Maintenance & Repairs",
        "query": "maintenance repairs painting plumbing electrical wear and tear",
    },
    {
        "id": "disputes",
        "label": "10. Dispute Resolution & Jurisdiction",
        "query": "dispute arbitration jurisdiction court governing law breach",
    },
]


def assess_document_review(con: sqlite3.Connection) -> ReviewResponse:
    """
    Evaluate the loaded document SQLite database across the Core 10 topics.
    Returns structured attention-first topics and neutral professional questions.
    """
    review_topics: List[ReviewTopic] = []
    evidence_by_topic: Dict[str, List[EvidenceItem]] = {}

    for cfg in CORE_10_TOPIC_CONFIG:
        topic_id = cfg["id"]
        label = cfg["label"]
        query = cfg["query"]

        gate = check_silence(con, topic=topic_id, query=query)

        evidence_items: List[EvidenceItem] = []
        for h in gate.hits[:4]:
            evidence_items.append(
                EvidenceItem(
                    sid=h.sid,
                    page=h.page_num,
                    section=h.section or "",
                    quote=h.sentence_text,
                    ocr_derived=False,
                )
            )

        evidence_by_topic[topic_id] = evidence_items

        status = "NOT_ASSESSED"
        attention_reason: Optional[str] = None

        if gate.status == STATUS_LOCATED:
            status = "FOUND"
            combined_text = " ".join(e.quote.lower() for e in evidence_items)

            # Heuristics for attention / tension detection
            if topic_id == "lock_in" and len(evidence_items) > 0:
                attention_reason = "Mandatory lock-in period specified; early termination may trigger penalties."
            elif topic_id == "notice":
                # Check for conflict between immediate termination vs notice or lockin
                if "lock" in combined_text and ("immediate" in combined_text or "without notice" in combined_text):
                    status = "POSSIBLE_CONFLICT"
                    attention_reason = "Clause contains both notice requirements and immediate termination/lock-in terms."
                elif len(evidence_items) > 1:
                    attention_reason = "Written notice period stipulated for agreement determination."
            elif topic_id == "deposit":
                if "forfeit" in combined_text or "non-refundable" in combined_text:
                    status = "POSSIBLE_CONFLICT"
                    attention_reason = "Potential deposit forfeiture or non-refundable condition specified."
                else:
                    attention_reason = "Security deposit terms located; inspect refund conditions."
            elif topic_id == "penalties" and len(evidence_items) > 0:
                attention_reason = "Late fees or default penalty charges stipulated."
            elif topic_id == "disputes" and len(evidence_items) > 0:
                attention_reason = "Designated court venue or arbitration mechanism specified."
            elif topic_id == "restrictions" and ("sublet" in combined_text or "commercial" in combined_text):
                attention_reason = "Subletting or use restrictions explicitly outlined."

        elif gate.status == STATUS_NOT_LOCATED:
            status = "NOT_FOUND"
        else:
            status = "NOT_ASSESSED"

        review_topics.append(
            ReviewTopic(
                topic_id=topic_id,
                label=label,
                status=status,
                evidence=evidence_items,
                attention_reason=attention_reason,
            )
        )

    # Cross-topic conflict detection: e.g. Notice vs Lock-in
    has_lockin = any(t.topic_id == "lock_in" and t.status == "FOUND" for t in review_topics)
    notice_topic = next((t for t in review_topics if t.topic_id == "notice"), None)
    if has_lockin and notice_topic and notice_topic.status == "FOUND":
        if not notice_topic.attention_reason:
            notice_topic.attention_reason = "Lock-in period coexists with notice clause; check interplay between lock-in and early exit."

    # Construct neutral, evidence-grounded professional questions
    prof_questions: List[ProfessionalQuestion] = []
    
    if evidence_by_topic.get("notice") or evidence_by_topic.get("lock_in"):
        prof_questions.append(
            ProfessionalQuestion(
                question_id="pq-notice-exit",
                text="Under what conditions may either party terminate this agreement prior to expiry without forfeiting the security deposit?",
                evidence=(evidence_by_topic.get("notice") or [])[:2],
            )
        )

    if evidence_by_topic.get("deposit"):
        prof_questions.append(
            ProfessionalQuestion(
                question_id="pq-deposit-refund",
                text="Within how many business days following handover of vacant possession must the security deposit be refunded, and what exact deduction conditions apply?",
                evidence=(evidence_by_topic.get("deposit") or [])[:2],
            )
        )

    if evidence_by_topic.get("maintenance"):
        prof_questions.append(
            ProfessionalQuestion(
                question_id="pq-maintenance-split",
                text="Which party is responsible for structural and society repairs versus internal day-to-day electrical and plumbing maintenance?",
                evidence=(evidence_by_topic.get("maintenance") or [])[:2],
            )
        )

    if evidence_by_topic.get("disputes"):
        prof_questions.append(
            ProfessionalQuestion(
                question_id="pq-disputes-venue",
                text="Which specific judicial jurisdiction or arbitration venue is designated to hear disputes arising under this agreement?",
                evidence=(evidence_by_topic.get("disputes") or [])[:2],
            )
        )

    return ReviewResponse(
        topics=review_topics,
        professional_questions=prof_questions,
    )
