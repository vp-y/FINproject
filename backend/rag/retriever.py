from qdrant_client.models import Filter, FieldCondition, MatchValue

from rag.embeddings import embeddings
from rag.vector_store import client, COLLECTION


def retrieve(query, company=None, top_k=5):

    # vector similarity search
    query_vector = embeddings.embed_query(query)

    query_filter = None

    if company:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="company",
                    match=MatchValue(value=company)
                )
            ]
        )

    response = client.query_points(
        collection_name=COLLECTION,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k
    )

    results = []

    for point in response.points:
        payload = dict(point.payload)
        text = payload.pop("text", "")
        results.append({
            "text": text,
            "metadata": payload,
            # Qdrant's cosine similarity score — used as the "relevance"
            # input to evidence_ranker.score_evidence() downstream.
            "score": point.score
        })

    return results
