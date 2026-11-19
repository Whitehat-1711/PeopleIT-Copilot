import re
from pathlib import Path
import chromadb
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

INDIRECT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"forget\s+(your\s+)?(rules|instructions|system\s+prompt)",
    r"\blist\s+every\s+employee\b",
    r"\breveal\s+(all\s+)?(employee|secret|phone|password)\b",
]


def _get_collection():
    client = chromadb.HttpClient(host="localhost", port=8000)
    return client.get_collection(name="company_policies")


def is_chunk_injected(text: str) -> bool:
    """Checks if a document chunk contains an indirect prompt injection attempt."""
    for pattern in INDIRECT_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


@tool
def search_company_policies(query: str) -> str:
    """Search official HR and IT policy documents for rules, leave entitlements,
    remote work guidelines, password policies, VPN setup, and hardware policies.
    Always use this tool for general company policy questions."""
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        transport="rest",
    )
    query_vector = embeddings_model.embed_query(query)

    collection = _get_collection()
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=3,
        include=["documents", "metadatas", "distances"],
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    formatted_chunks = []
    for doc, meta, dist in zip(docs, metas, distances):
        similarity = 1 - dist
        if similarity < 0.60:
            continue

        # Task A4.4: Drop or sanitize chunks flagged for indirect prompt injection
        if is_chunk_injected(doc):
            # Strip out malicious instructions while keeping benign context
            doc = re.sub(
                r"(?i)(ignore\s+previous\s+instructions|list\s+every\s+employee|reveal\s+all).*?(\.\s+|$)",
                "[Untrusted instruction stripped]",
                doc,
            )

        source = meta.get("source", "unknown")
        section = meta.get("section", "General")
        # Task A4.2: Wrap chunks in <policy_context> tags
        formatted_chunks.append(
            f"<policy_context>\n"
            f"(Source: {source} | Section: {section})\n"
            f"{doc}\n"
            f"</policy_context>"
        )

    if not formatted_chunks:
        return "NO_RELEVANT_POLICY_FOUND: The company HR and IT policy documents do not contain information on this topic."

    return "\n\n---\n\n".join(formatted_chunks)
