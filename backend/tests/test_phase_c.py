"""
Test suite for Phase C: RAG & Answer Quality (Tasks C1 - C6)
"""

import os
from pathlib import Path
import pytest

from backend.agent import AgentResponse, check_groundedness, run_agent
from backend.rag import (
    SIMILARITY_THRESHOLD,
    TOP_K_RESULTS,
    get_retrieved_sources,
    rewrite_query,
    search_company_policies,
)
from backend.ticket_tools import AUDIT_LOG_FILE, create_ticket_record

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR.parent / "data"


# ============================================================================
# Task C1: Richer Policy Corpus & No Sabbatical
# ============================================================================
def test_c1_corpus_has_at_least_5_files():
    files = list(DATA_DIR.glob("*.md"))
    assert len(files) >= 5, f"Expected at least 5 files, found {len(files)}"
    expected_files = {
        "hr_policy.md",
        "it_policy.md",
        "expenses_travel_policy.md",
        "onboarding_offboarding_policy.md",
        "code_of_conduct.md",
        "data_handling_policy.md",
    }
    actual_names = {f.name for f in files}
    assert expected_files.issubset(actual_names)


def test_c1_files_have_owner_and_last_updated():
    for md_file in DATA_DIR.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        assert "Owner:" in content, f"{md_file.name} is missing Owner line"
        assert "Last-Updated:" in content, f"{md_file.name} is missing Last-Updated line"


def test_c1_sabbatical_does_not_exist_in_corpus():
    """Confirms the unanswerable topic (sabbatical) genuinely does not exist."""
    for md_file in DATA_DIR.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        assert "sabbatical" not in content.lower(), (
            f"Found forbidden term 'sabbatical' in {md_file.name}"
        )


# ============================================================================
# Task C2: Structured Answers with Citations
# ============================================================================
def test_c2_structured_response_structure():
    resp = AgentResponse({
        "answer": "Test answer",
        "sources": [{"document": "hr_policy.md", "section": "Annual Leave"}],
        "route": "rag",
        "confidence": 0.95,
        "status": "allowed",
    })
    assert isinstance(resp, dict)
    assert resp["answer"] == "Test answer"
    assert resp.answer == "Test answer"
    assert str(resp) == "Test answer"
    assert resp["route"] == "rag"
    assert resp["confidence"] == 0.95
    assert len(resp["sources"]) == 1
    assert resp["sources"][0]["document"] == "hr_policy.md"


# ============================================================================
# Task C3: Retrieval Tuning & Query Rewriting
# ============================================================================
def test_c3_threshold_and_top_k():
    assert SIMILARITY_THRESHOLD == 0.60
    assert TOP_K_RESULTS >= 4


def test_c3_query_rewrite_short_and_long():
    short_q = "vpn setup"
    expanded = rewrite_query(short_q)
    assert "WireGuard" in expanded or "VPN" in expanded
    assert len(expanded) > len(short_q)

    long_q = "How do I submit an expense report for my recent domestic flight travel?"
    same_q = rewrite_query(long_q)
    assert same_q == long_q


# ============================================================================
# Task C4: Escalation Instead of Dead End
# ============================================================================
def test_c4_create_ticket_writes_to_postgres_and_audit():
    info = create_ticket_record(
        category="HR",
        summary="Employee inquiry regarding sabbatical leave policy",
        emp_id="E102",
    )
    assert info["ticket_id"].startswith("HR-")
    assert info["emp_id"] == "E102"
    assert "People Operations" in info["contact"]
    assert info["status"] == "OPEN"

    # Verify audit log
    assert AUDIT_LOG_FILE.exists()
    audit_content = AUDIT_LOG_FILE.read_text(encoding="utf-8")
    assert info["ticket_id"] in audit_content
    assert "sabbatical leave policy" in audit_content


# ============================================================================
# Task C5: Groundedness Check
# ============================================================================
def test_c5_groundedness_passes_for_supported_claim():
    context = (
        "Full-time employees receive 24 days of paid annual leave per calendar year, "
        "accrued at a rate of 2 days per month."
    )
    answer = "According to company policy, full-time employees are entitled to 24 days of annual leave each year."
    assert check_groundedness(answer, context) is True


def test_c5_groundedness_fails_for_unsupported_hallucination():
    context = (
        "Full-time employees receive 24 days of paid annual leave per calendar year."
    )
    unsupported_answer = "Employees can take unlimited paid leave anytime and get a free company helicopter ride."
    assert check_groundedness(unsupported_answer, context) is False


# ============================================================================
# Task C6: Clean Hybrid Query Execution
# ============================================================================
@pytest.mark.asyncio
async def test_c6_hybrid_case_regression():
    """
    Test case #6: For 'Can I take 5 days off?', agent must:
    1. Query leave balance (E102 has 6 days)
    2. Query annual leave policy (1-5 days requires manager approval 5 business days in advance)
    3. Compare and answer quoting both facts.
    """
    resp = await run_agent("Can I take 5 days off?", emp_id="E102")

    assert resp["route"] == "hybrid"
    assert resp["status"] == "allowed"
    assert len(resp["sources"]) >= 1

    answer = resp["answer"].lower()
    # Must quote/mention balance of 6 days
    assert "6" in answer, "Answer must reference employee's 6 days leave balance"
    # Must mention notice/approval requirement
    assert ("approval" in answer or "notice" in answer or "advance" in answer or "manager" in answer)
