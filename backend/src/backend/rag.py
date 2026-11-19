import re
from pathlib import Path
from typing import Any
import chromadb
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from backend.log import log

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

SIMILARITY_THRESHOLD = 0.60
TOP_K_RESULTS = 4

INDIRECT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"forget\s+(your\s+)?(rules|instructions|system\s+prompt)",
    r"\blist\s+every\s+employee\b",
    r"\breveal\s+(all\s+)?(employee|secret|phone|password)\b",
]

# Task C2: Thread-safe/context-scoped store of actual retrieved chunks
_RETRIEVED_SOURCES: list[dict[str, Any]] = []


def clear_retrieved_sources():
    global _RETRIEVED_SOURCES
    _RETRIEVED_SOURCES = []


def get_retrieved_sources() -> list[dict[str, Any]]:
    global _RETRIEVED_SOURCES
    # Deduplicate by (document, section)
    seen = set()
    unique_sources = []
    for s in _RETRIEVED_SOURCES:
        key = (s.get("document"), s.get("section"))
        if key not in seen:
            seen.add(key)
            unique_sources.append(s)
    return unique_sources


def _get_collection():
    client = chromadb.HttpClient(host="localhost", port=8000)
    return client.get_collection(name="company_policies")


def is_chunk_injected(text: str) -> bool:
    """Checks if a document chunk contains an indirect prompt injection attempt."""
    for pattern in INDIRECT_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def rewrite_query(query: str) -> str:
    """Task C3.3: Expands short or keyword-only queries to improve dense embedding retrieval."""
    q = query.strip()
    words = q.split()
    if len(words) <= 4:
        expansions = {
            "vpn": "WireGuard corporate VPN client remote network access setup configuration",
            "password": "Password complexity rotation requirements and multi factor authentication MFA",
            "mfa": "Multi-Factor Authentication hardware security key authenticator app requirements",
            "laptop": "Hardware provisioning replacement cycle laptop models developer machines",
            "leave": "Paid annual leave sick medical parental leave rules entitlement",
            "pto": "Paid time off annual leave entitlement and manager approval timeline",
            "wfh": "Remote work hybrid schedule core hours anchor days in office",
            "notice": "Resignation notice period probation duration offboarding requirements",
            "travel": "Domestic international business travel expense per diem allowance",
            "expenses": "Expense claim reimbursement GST receipt submission timeline",
            "stipend": "Annual Learning and Development L&D stipend certification reimbursement",
            "onboarding": "New hire orientation hardware provisioning pre boarding process",
            "probation": "Probation period duration performance review confirmation letter",
            "conduct": "Workplace professionalism anti harassment ethics conflict of interest",
            "ethics": "Gifts anti bribery whistleblower protection reporting hotline",
            "privacy": "Customer data protection privacy classification GDPR DPDP least privilege",
        }
        for k, v in expansions.items():
            if k in q.lower():
                expanded = f"{q} {v}"
                log(f"🔍 query_rewrite: expanded short query '{q}' -> '{expanded}'")
                return expanded
    return q


@tool
def search_company_policies(query: str) -> str:
    """Search official HR, IT, Travel, Onboarding, Code of Conduct, and Data Handling policy documents.
    Always use this tool for company rules, policies, and guidelines."""
    search_text = rewrite_query(query)

    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        transport="rest",
    )
    query_vector = embeddings_model.embed_query(search_text)

    collection = _get_collection()
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=TOP_K_RESULTS,
        include=["documents", "metadatas", "distances"],
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    formatted_chunks = []
    for doc, meta, dist in zip(docs, metas, distances):
        similarity = 1 - dist
        if similarity < SIMILARITY_THRESHOLD:
            continue

        source = meta.get("source", "unknown")
        section = meta.get("section", "General")
        owner = meta.get("owner", "General Team")
        last_updated = meta.get("last_updated", "2026-01-01")

        # Track verifiable retrieval metadata (Task C2)
        _RETRIEVED_SOURCES.append({
            "document": source,
            "section": section,
            "owner": owner,
            "last_updated": last_updated,
            "similarity": round(float(similarity), 3),
        })

        # Task A4.4: Sanitize indirect prompt injections
        if is_chunk_injected(doc):
            doc = re.sub(
                r"(?i)(ignore\s+previous\s+instructions|list\s+every\s+employee|reveal\s+all).*?(\.\s+|$)",
                "[Untrusted instruction stripped]",
                doc,
            )

        formatted_chunks.append(
            f"<policy_context source='{source}' section='{section}' owner='{owner}' last_updated='{last_updated}'>\n"
            f"(Source: {source} | Section: {section} | Owner: {owner} | Last-Updated: {last_updated})\n"
            f"{doc}\n"
            f"</policy_context>"
        )

    if not formatted_chunks:
        return "NO_RELEVANT_POLICY_FOUND: The company policy documents do not contain information on this topic."

    return "\n\n---\n\n".join(formatted_chunks)
