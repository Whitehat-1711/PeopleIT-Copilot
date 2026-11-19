from pathlib import Path
import chromadb
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"

load_dotenv(BACKEND_DIR / ".env")


def ingest_documents() -> None:
    client = chromadb.HttpClient(host="localhost", port=8000)

    # Reset collection on re-ingest to avoid duplicate chunks
    try:
        client.delete_collection("company_policies")
    except Exception:
        pass

    collection = client.create_collection(
        name="company_policies",
        metadata={"hnsw:space": "cosine"},
    )

    splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("##", "section"),
    ],
    strip_headers=False,
)

    all_chunks = []
    for md_file in sorted(DATA_DIR.glob("*.md")):
        raw_text = md_file.read_text(encoding="utf-8")
        chunks = splitter.split_text(raw_text)
        for chunk in chunks:
            chunk.metadata["source"] = md_file.name
            all_chunks.append(chunk)

    if not all_chunks:
        raise RuntimeError(f"No markdown documents found in {DATA_DIR}")

    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        transport="rest",
    )

    texts = [c.page_content for c in all_chunks]
    metadatas = [c.metadata for c in all_chunks]
    ids = [f"doc_{i}" for i in range(len(all_chunks))]
    vectors = embeddings_model.embed_documents(texts)

    collection.add(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
        embeddings=vectors,
    )
    print(f"Indexed {len(all_chunks)} policy sections into Docker ChromaDB.")


if __name__ == "__main__":
    ingest_documents()