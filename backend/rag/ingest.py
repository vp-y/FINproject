import time
from pathlib import Path

from rag.indexer import index_document
from rag.embeddings import embeddings
from rag.vector_store import upsert_chunks

# Gemini's free-tier embedding quota is 100 requests/minute (and 1000/day),
# and embed_documents() makes one request per text under the hood — so we
# stay a bit under the per-minute limit per batch and pause between
# batches to let the window reset.
RATE_LIMIT_BATCH = 90
RATE_LIMIT_PAUSE_SECONDS = 65

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "documents"

DOCUMENTS = [
    {
        "path": str(DATA_DIR / "AAPL_Annual_Report.pdf"),
        "document_name": "Apple Annual Report 2025",
        "company": "Apple",
        "document_type": "Annual Report",
        "year": 2025
    },
    {
        "path": str(DATA_DIR / "NVIDIA_Annual_Report.pdf"),
        "document_name": "NVIDIA Annual Report 2025",
        "company": "NVIDIA",
        "document_type": "Annual Report",
        "year": 2025
    },
    {
        "path": str(DATA_DIR / "FED_Monetary_Report.pdf"),
        "document_name": "Federal Reserve Monetary Policy Report July 2026",
        "company": "Federal Reserve",
        "document_type": "Monetary Policy Report",
        "year": 2026
    }
]


def embed_with_retry(texts, attempts=3):

    for attempt in range(1, attempts + 1):
        try:
            return embeddings.embed_documents(texts)
        except Exception as e:
            if attempt == attempts:
                raise
            print(f"    embed error ({e.__class__.__name__}), "
                  f"waiting {RATE_LIMIT_PAUSE_SECONDS}s and retrying "
                  f"(attempt {attempt}/{attempts})...")
            time.sleep(RATE_LIMIT_PAUSE_SECONDS)


def embed_and_store(chunks, batch_size=RATE_LIMIT_BATCH):
    """Embeds and upserts a list of {"text", "metadata"} chunks,
    rate-limited. Shared by both bulk ingestion and single-document
    ingestion (used by data_pipeline after a fresh download)."""

    total_batches = (len(chunks) + batch_size - 1) // batch_size

    for batch_num, i in enumerate(range(0, len(chunks), batch_size), start=1):

        batch = chunks[i:i + batch_size]
        texts = [c["text"] for c in batch]

        vectors = embed_with_retry(texts)

        upsert_chunks(batch, vectors)

        print(f"  batch {batch_num}/{total_batches}: "
              f"upserted {min(i + batch_size, len(chunks))}/{len(chunks)}")

        if batch_num < total_batches:
            time.sleep(RATE_LIMIT_PAUSE_SECONDS)


def ingest_document(path, document_name, company, document_type, year):
    """Index + embed + store a single document — the 'automatically
    trigger RAG ingestion' step that runs right after data_pipeline
    downloads a new report."""

    chunks = index_document(
        path,
        document_name=document_name,
        company=company,
        document_type=document_type,
        year=year
    )

    embed_and_store(chunks)

    return len(chunks)


def ingest_all():

    # Build the full chunk list across all documents first, so batches
    # (and thus rate-limit pauses) span document boundaries cleanly
    # instead of resetting per document.
    all_chunks = []

    for doc in DOCUMENTS:

        print(f"Indexing {doc['document_name']}...")

        chunks = index_document(
            doc["path"],
            document_name=doc["document_name"],
            company=doc["company"],
            document_type=doc["document_type"],
            year=doc["year"]
        )

        all_chunks.extend(chunks)

    print(f"Total chunks to embed: {len(all_chunks)}")

    embed_and_store(all_chunks)

    print("Ingestion complete.")


if __name__ == "__main__":
    ingest_all()
