"""
Task D1: FastAPI Service for Enterprise HR & IT Assistant.
Provides endpoints for chat, streaming SSE, employee switcher, health, audit logs, and feedback.
"""

import asyncio
from contextlib import asynccontextmanager
import json
import os
from typing import Any
import chromadb
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import psycopg
from pydantic import BaseModel, Field

from backend.agent import get_or_build_graph, run_agent
from backend.audit import get_audit_logs, save_feedback
from backend.log import log
from backend.resilience import RateLimiter

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

# Rate limiter: maximum 30 requests per minute per employee
rate_limiter = RateLimiter(max_requests=30, window_seconds=60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan handler: Pre-warms the agent graph and MCP clients once on startup
    to prevent latency spikes on first request.
    """
    log("🚀 Starting FastAPI service — pre-warming agent graphs for demo users...")
    try:
        # Pre-warm demo employees
        for emp_id in ["E101", "E102", "E103"]:
            await get_or_build_graph(emp_id)
        log("✅ Pre-warming complete — Agent & MCP clients initialized.")
    except Exception as e:
        log(f"⚠️ Pre-warming warning (will initialize on demand): {e}")

    yield
    log("🛑 Shutting down FastAPI service.")


app = FastAPI(
    title="Enterprise HR & IT AI Assistant API",
    version="1.0.0",
    description="Backend API powering HR/IT self-service chat, streaming responses, audit trail, and feedback.",
    lifespan=lifespan,
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Request / Response Schemas
# ============================================================================
class ChatRequest(BaseModel):
    message: str = Field(..., description="User question or inquiry")
    emp_id: str = Field(..., description="Authenticated employee ID, e.g. E102")
    thread_id: str | None = Field(default=None, description="Optional conversation session ID")


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]]
    route: str
    status: str
    ticket_id: str | None = None
    thread_id: str
    audit_id: int | None = None


class FeedbackRequest(BaseModel):
    audit_id: int | None = Field(default=None, description="Audit turn ID being reviewed")
    rating: str = Field(..., description="'up' or 'down'")
    comment: str | None = Field(default=None, description="Optional user comment")


# ============================================================================
# API Endpoints
# ============================================================================
@app.get("/health")
def health_check():
    """Service health verification inspecting Postgres and ChromaDB connectivity."""
    postgres_ok = False
    chromadb_ok = False

    try:
        with psycopg.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                postgres_ok = True
    except Exception as e:
        log(f"⚠️ Health check Postgres error: {e}")

    try:
        client = chromadb.HttpClient(host="localhost", port=8000)
        client.heartbeat()
        chromadb_ok = True
    except Exception as e:
        log(f"⚠️ Health check ChromaDB error: {e}")

    status = "ok" if (postgres_ok and chromadb_ok) else "degraded"
    return {
        "status": status,
        "postgres": postgres_ok,
        "chromadb": chromadb_ok,
    }


@app.get("/employees")
def list_employees():
    """Returns directory of demo employees for frontend identity switcher."""
    try:
        demo_ids = ["E101", "E102", "E103", "E104", "E105"]
        employees = []
        with psycopg.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                for eid in demo_ids:
                    cur.execute(
                        "SET app.emp_id = %s; SELECT emp_id, full_name, department, laptop_model FROM v_self_service;",
                        (eid,),
                    )
                    row = cur.fetchone()
                    if row:
                        employees.append({
                            "id": row[0],
                            "name": row[1],
                            "department": row[2],
                            "laptop": row[3],
                            "role": f"{row[2]} Lead" if "Eng" in row[2] else f"{row[2]} Specialist",
                        })
        if employees:
            return employees
    except Exception as e:
        log(f"⚠️ Error querying employees with session setting: {e}")

    return [
        {"id": "E101", "name": "Aarav Sharma", "department": "Engineering", "role": "Engineering Lead"},
        {"id": "E102", "name": "Priya Patel", "department": "Marketing", "role": "Marketing Specialist"},
        {"id": "E103", "name": "Rohan Verma", "department": "Finance", "role": "Financial Analyst"},
    ]


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """Primary chat endpoint taking message, emp_id, and thread_id."""
    rate_limiter.check_rate_limit(req.emp_id)

    resp = await run_agent(
        message=req.message,
        emp_id=req.emp_id,
        thread_id=req.thread_id,
    )

    return ChatResponse(
        answer=resp.get("answer", ""),
        sources=resp.get("sources", []),
        route=resp.get("route", "direct"),
        status=resp.get("status", "allowed"),
        ticket_id=resp.get("ticket_id"),
        thread_id=resp.get("thread_id", ""),
        audit_id=resp.get("audit_id"),
    )


@app.post("/chat/stream")
async def chat_stream_endpoint(req: ChatRequest):
    """Server-Sent Events (SSE) streaming endpoint rendering answers token-by-token."""
    rate_limiter.check_rate_limit(req.emp_id)

    async def sse_event_generator():
        try:
            resp = await run_agent(
                message=req.message,
                emp_id=req.emp_id,
                thread_id=req.thread_id,
            )

            answer = resp.get("answer", "")
            # Stream words with light pacing for smooth UI rendering
            words = answer.split(" ")
            for i, word in enumerate(words):
                chunk = word if i == 0 else " " + word
                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
                await asyncio.sleep(0.01)

            # Emit final completion packet with full metadata
            done_payload = {
                "type": "done",
                "answer": answer,
                "sources": resp.get("sources", []),
                "route": resp.get("route", "direct"),
                "status": resp.get("status", "allowed"),
                "ticket_id": resp.get("ticket_id"),
                "thread_id": resp.get("thread_id"),
                "audit_id": resp.get("audit_id"),
            }
            yield f"data: {json.dumps(done_payload)}\n\n"
        except Exception as e:
            error_payload = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(sse_event_generator(), media_type="text/event-stream")


@app.get("/audit")
def audit_endpoint(limit: int = Query(default=50, ge=1, le=500)):
    """Admin view endpoint retrieving recent turn records."""
    logs = get_audit_logs(limit=limit)
    return {"count": len(logs), "logs": logs}


@app.post("/feedback")
def feedback_endpoint(req: FeedbackRequest):
    """Records user thumbs up/down and comments for audit turns."""
    res = save_feedback(
        audit_id=req.audit_id,
        rating=req.rating,
        comment=req.comment,
    )
    return res
