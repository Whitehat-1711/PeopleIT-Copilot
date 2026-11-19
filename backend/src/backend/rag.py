from pathlib import Path
import chromadb
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


def _get_collection():
    client = chromadb.HttpClient(host="localhost", port=8000)
    return client.get_collection(name="company_policies")


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
        source = meta.get("source", "unknown")
        section = meta.get("section", "General")
        formatted_chunks.append(f"(Source: {source} | Section: {section})\n{doc}")

    if not formatted_chunks:
        return "NO_RELEVANT_POLICY_FOUND: The company HR and IT policy documents do not contain information on this topic."

    return "\n\n---\n\n".join(formatted_chunks)