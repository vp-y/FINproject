from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


SOURCE_WEIGHTS = {

    "regulatory_filing": 1.0,

    "company_website": 0.9,

    "major_news": 0.8,

    "general_news": 0.6,

    # Step 5.12 lists these as valid source_types too, but the original
    # weights only covered four of the six — added so they don't
    # silently fall through to the 0.5 unknown-type default.
    "market_data": 1.0,       # objective figures, not a claim to weigh
    "internal_document": 0.9,

}


def score_evidence(
    source_type: str,
    relevance: float,
    recency: float,
) -> float:

    source_score = SOURCE_WEIGHTS.get(
        source_type,
        0.5,
    )

    return (
        source_score
        * relevance
        * recency
    )


def compute_recency(published_at, half_life_days: float = 14) -> float:
    """Exponential decay — an article from today scores ~1.0, one from
    half_life_days ago scores ~0.5. Items with no timestamp (annual
    reports, market snapshots) get full recency rather than being
    unfairly penalized for a field that doesn't apply to them."""

    if not published_at:
        return 1.0

    published = None

    try:
        # Tavily/news timestamps look like "Fri, 21 Aug 2026 02:00:00 GMT"
        published = parsedate_to_datetime(published_at)
    except (TypeError, ValueError):
        try:
            published = datetime.fromisoformat(
                str(published_at).replace("Z", "+00:00")
            )
        except ValueError:
            return 1.0

    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)

    age_days = (
        datetime.now(timezone.utc) - published
    ).total_seconds() / 86400

    return 0.5 ** (max(age_days, 0) / half_life_days)


def _evidence_key(item: dict):
    """De-duplication key. The research agent has its own copy of
    analyze_recent_market_move (Step 5.9), so the same ticker's move can
    get recorded both by the workflow's own deterministic Step 5 call
    and independently by the LLM agent choosing to call it again —
    same fact, would otherwise show up twice."""

    source_type = item.get("source_type")

    if source_type == "market_data":
        return (source_type, item.get("ticker"))

    if source_type in ("regulatory_filing", "internal_document"):
        return (source_type, item.get("title"), item.get("page"))

    return (source_type, item.get("url") or item.get("title"))


def rank_evidence(items: list[dict]) -> list[dict]:
    """Scores, de-duplicates, and sorts a flat list of evidence items
    (each tagged with source_type, and carrying 'relevance'/
    'published_at' where applicable) using the Source Quality x
    Relevance x Recency model."""

    seen = set()
    deduped = []

    for item in items:

        key = _evidence_key(item)

        if key in seen:
            continue

        seen.add(key)
        deduped.append(item)

    ranked = []

    for item in deduped:

        relevance = item.get("relevance", 0.7)
        recency = compute_recency(item.get("published_at"))

        score = score_evidence(
            source_type=item.get("source_type", "general_news"),
            relevance=relevance,
            recency=recency,
        )

        ranked.append({**item, "score": round(score, 4)})

    ranked.sort(key=lambda entry: entry["score"], reverse=True)

    return ranked
