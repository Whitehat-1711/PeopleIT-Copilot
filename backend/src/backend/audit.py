"""
Task D3 & D4: Audit logging and user feedback management.
Records every conversation turn into PostgreSQL audit_log with PII redaction,
and manages user feedback submissions.
"""

import json
import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
import psycopg

from backend.guardrails import redact_pii
from backend.log import log

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")
DB_URL = os.getenv("DATABASE_URL")


def log_audit_turn(
    *,
    emp_id: str,
    thread_id: str,
    question: str,
    route: str,
    status: str,
    guardrail_triggered: bool = False,
    tools_used: list[str] | None = None,
    sources: list[dict[str, Any]] | None = None,
    latency_ms: int = 0,
) -> int:
    """
    Writes a single turn record to PostgreSQL audit_log table.
    Redacts any sensitive PII from the user's question before persisting.
    Returns the generated audit record ID.
    """
    redacted_question, _ = redact_pii(question, current_emp_id=emp_id)
    tools_json = json.dumps(tools_used or [])
    sources_json = json.dumps(sources or [])

    try:
        with psycopg.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO audit_log (
                        emp_id, thread_id, question, route, status,
                        guardrail_triggered, tools_used, sources, latency_ms
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s)
                    RETURNING id;
                    """,
                    (
                        emp_id,
                        thread_id,
                        redacted_question,
                        route,
                        status,
                        guardrail_triggered,
                        tools_json,
                        sources_json,
                        latency_ms,
                    ),
                )
                audit_id = cur.fetchone()[0]
                conn.commit()
                log(f"📋 AUDIT_LOG: recorded turn #{audit_id} for {emp_id} [{route}] ({latency_ms}ms)")
                return audit_id
    except Exception as e:
        log(f"⚠️ Failed to write audit_log: {e}")
        return -1


def get_audit_logs(limit: int = 50) -> list[dict[str, Any]]:
    """Retrieves recent audit logs for administrative inspection."""
    try:
        with psycopg.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, ts, emp_id, thread_id, question, route,
                           status, guardrail_triggered, tools_used, sources, latency_ms
                    FROM audit_log
                    ORDER BY ts DESC
                    LIMIT %s;
                    """,
                    (limit,),
                )
                cols = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                results = []
                for row in rows:
                    item = dict(zip(cols, row))
                    if item.get("ts"):
                        item["ts"] = item["ts"].isoformat()
                    results.append(item)
                return results
    except Exception as e:
        log(f"⚠️ Failed to read audit_log: {e}")
        return []


def save_feedback(audit_id: int | None, rating: str, comment: str | None = None) -> dict[str, Any]:
    """Saves user rating ('up' or 'down') and optional comment to feedback table."""
    rating_clean = rating.strip().lower()
    if rating_clean not in {"up", "down"}:
        rating_clean = "up" if "up" in rating_clean else "down"

    try:
        with psycopg.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO feedback (audit_id, rating, comment)
                    VALUES (%s, %s, %s)
                    RETURNING id, created_at;
                    """,
                    (audit_id, rating_clean, comment),
                )
                row = cur.fetchone()
                conn.commit()
                feedback_id = row[0]
                ts = row[1].isoformat() if row[1] else None
                log(f"👍 FEEDBACK: #{feedback_id} audit_id={audit_id} rating={rating_clean}")
                return {
                    "id": feedback_id,
                    "audit_id": audit_id,
                    "rating": rating_clean,
                    "comment": comment,
                    "created_at": ts,
                }
    except Exception as e:
        log(f"⚠️ Failed to save feedback: {e}")
        return {
            "id": -1,
            "audit_id": audit_id,
            "rating": rating_clean,
            "comment": comment,
            "error": str(e),
        }
