"""
Parameterized employee tools providing zero-argument lookup functions.
These tools do not accept any employee ID parameter from the model;
they look up records exclusively for the session-scoped emp_id.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.tools import tool

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


def create_employee_tools(emp_id: str) -> list:
    """Creates a suite of employee self-service tools hard-bound to emp_id."""
    import psycopg

    db_url = os.getenv("DATABASE_URL")

    def _query(sql: str, params: tuple = ()) -> list[dict]:
        with psycopg.connect(db_url, options=f"-c app.emp_id={emp_id}") as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                cols = [desc[0] for desc in cur.description] if cur.description else []
                rows = cur.fetchall()
                return [dict(zip(cols, row)) for row in rows]

    @tool
    def get_my_leave_balance() -> str:
        """Get the current employee's remaining leave balance in days.
        Takes no arguments; automatically looks up the authenticated user."""
        rows = _query("SELECT full_name, leave_balance FROM v_self_service;")
        if not rows:
            return "No employee record found for your identity."
        return f"Employee {rows[0]['full_name']} has {rows[0]['leave_balance']} days of paid leave remaining."

    @tool
    def get_my_laptop() -> str:
        """Get the laptop model assigned to the current employee.
        Takes no arguments; automatically looks up the authenticated user."""
        rows = _query("SELECT full_name, laptop_model FROM v_self_service;")
        if not rows:
            return "No employee record found for your identity."
        return f"Employee {rows[0]['full_name']} is assigned hardware: {rows[0]['laptop_model']}."

    @tool
    def get_my_profile() -> str:
        """Get the current employee's profile including full name, department, leave balance, and laptop model.
        Takes no arguments; automatically looks up the authenticated user."""
        rows = _query("SELECT emp_id, full_name, department, leave_balance, laptop_model FROM v_self_service;")
        if not rows:
            return "No employee record found for your identity."
        r = rows[0]
        return (
            f"Employee ID: {r['emp_id']}\n"
            f"Name: {r['full_name']}\n"
            f"Department: {r['department']}\n"
            f"Leave Balance: {r['leave_balance']} days\n"
            f"Assigned Laptop: {r['laptop_model']}"
        )

    return [get_my_leave_balance, get_my_laptop, get_my_profile]
