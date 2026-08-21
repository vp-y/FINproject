import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

client = QdrantClient(
    host="localhost",
    port=6333
)

COLLECTION = "financial_documents"

# gemini-embedding-001 output size (see rag/embeddings.py)
VECTOR_SIZE = 3072


def ensure_collection():

    if client.collection_exists(COLLECTION):
        return

    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE
        )
    )


def upsert_chunks(chunks, vectors):
    """chunks: list of {"text": ..., "metadata": {...}} (see rag/indexer.py)
    vectors: matching list of embedding vectors, same order/length."""

    ensure_collection()

    points = []

    for chunk, vector in zip(chunks, vectors):

        payload = dict(chunk["metadata"])
        payload["text"] = chunk["text"]

        # Deterministic ID from chunk_id (not a random uuid4) so that
        # re-running ingestion after an interruption overwrites the same
        # points instead of duplicating them.
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, payload["chunk_id"]))

        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )
        )

    client.upsert(
        collection_name=COLLECTION,
        points=points
    )
