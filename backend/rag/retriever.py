from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny

from rag.embeddings import embeddings
from rag.vector_store import client, COLLECTION


def retrieve(query, company=None, companies=None, ticker=None, tickers=None, top_k=5):
    """Vector similarity search, optionally filtered by company name(s)
    or ticker(s).

    `companies`/`tickers` (a list, matched via Qdrant's MatchAny) take
    precedence over the single-value `company`/`ticker` (MatchValue)
    params when both are given for the same field — existing callers
    that only ever pass `company=` see identical behavior to before.

    `ticker`/`tickers` filters on the `ticker` metadata field (only
    present on documents ingested through the per-holding onboarding
    pipeline — see rag/indexer.py); `company`/`companies` filters on the
    older `company` display-name field (present on every indexed
    document, including the three bulk-seeded ones with no ticker at
    all). Prefer ticker-based filtering where the caller has real
    tickers on hand — it's an exact identifier, not a fuzzy name match."""

    query_vector = embeddings.embed_query(query)

    conditions = []

    if companies:
        conditions.append(
            FieldCondition(key="company", match=MatchAny(any=companies))
        )
    elif company:
        conditions.append(
            FieldCondition(key="company", match=MatchValue(value=company))
        )

    if tickers:
        conditions.append(
            FieldCondition(key="ticker", match=MatchAny(any=tickers))
        )
    elif ticker:
        conditions.append(
            FieldCondition(key="ticker", match=MatchValue(value=ticker))
        )

    query_filter = Filter(must=conditions) if conditions else None

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
