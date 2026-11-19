"""
Task C4: Ticket escalation tool and audit logging.
When policy search finds no matching rule or DB has no record,
the agent can escalate by creating a ticket in PostgreSQL.
"""

import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.tools import tool
import psycopg

from backend.log import log

BACKEND_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = BACKEND_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
AUDIT_LOG_FILE = LOG_DIR / "audit.log"

load_dotenv(BACKEND_DIR / ".env")
DB_URL = os.getenv("DATABASE_URL")

CONTACT_DIRECTORY = {
    "HR": "People Operations (hr@company.com)",
    "IT": "IT Support Desk (it-helpdesk@company.com)",
    "FINANCE": "Finance & Expense Desk (finance@company.com)",
    "LEGAL": "Legal & Compliance (compliance@company.com)",
}


def audit_log(event: str, details: dict) -> None:
    """Appends an event record to the audit log."""
    ts = datetime.now().isoformat()
    record = f"[{ts}] {event.upper()}: {details}\n"
    with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(record)
    log(f"📝 AUDIT: {event} -> {details}")


def create_ticket_record(category: str, summary: str, emp_id: str) -> dict:
    """Inserts a ticket into Postgres tickets table and records audit log."""
    cat_clean = category.strip().upper() if category else "HR"
    prefix = "IT" if "IT" in cat_clean else ("FIN" if "FIN" in cat_clean else "HR")

    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM tickets;")
            count = cur.fetchone()[0]
            ticket_id = f"{prefix}-{1040 + count + 1}"

            cur.execute(
                """
                INSERT INTO tickets (ticket_id, emp_id, category, summary, status)
                VALUES (%s, %s, %s, %s, 'OPEN')
                RETURNING ticket_id, created_at;
                """,
                (ticket_id, emp_id, cat_clean, summary),
            )
            res = cur.fetchone()
            conn.commit()

    contact = CONTACT_DIRECTORY.get(prefix, "Internal Helpdesk (helpdesk@company.com)")
    ticket_info = {
        "ticket_id": ticket_id,
        "emp_id": emp_id,
        "category": cat_clean,
        "summary": summary,
        "contact": contact,
        "status": "OPEN",
    }
    audit_log("ticket_created", ticket_info)
    return ticket_info


def make_ticket_tool(emp_id: str):
    """Creates a ticket creation tool bound to the session emp_id."""

    @tool
    def create_support_ticket(category: str, summary: str) -> str:
        """Create an escalation support ticket when an HR or IT policy is not found or a record is missing.
        Args:
            category: 'HR', 'IT', or 'Finance'
            summary: Brief description of the issue or unanswered question
        """
        info = create_ticket_record(category=category, summary=summary, emp_id=emp_id)
        return (
            f"TICKET_CREATED:\n"
            f"Ticket ID: {info['ticket_id']}\n"
            f"Category: {info['category']}\n"
            f"Status: OPEN\n"
            f"Contact: {info['contact']}\n"
            f"Message: Your question has been escalated. A representative from {info['contact']} will follow up."
        )

    return create_support_ticket
