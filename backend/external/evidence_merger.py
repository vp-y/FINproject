MAJOR_NEWS_DOMAINS = {
    "reuters.com", "bloomberg.com", "wsj.com", "cnbc.com", "ft.com",
    "apnews.com", "nytimes.com", "marketwatch.com",
}


def build_evidence_items(tool_results: list[dict]) -> list[dict]:
    """Converts the raw tool_results captured by the orchestrator (see
    agent_orchestrator.run_agent) into the canonical, source_type-tagged
    shape from Step 5.12, ready for evidence_ranker.rank_evidence()."""

    items = []

    for tool_result in tool_results:

        tool = tool_result["tool"]
        result = tool_result["result"]

        if tool == "search_financial_documents":

            for chunk in result.get("results", []):

                metadata = chunk.get("metadata", {})

                items.append({
                    "source_type": "regulatory_filing",
                    "title": metadata.get("document_name"),
                    "company": metadata.get("company"),
                    "page": metadata.get("page_number"),
                    "published_at": None,
                    "url": None,
                    "relevance": chunk.get("score", 0.7),
                    "text": chunk.get("text"),
                })

        elif tool == "analyze_recent_market_move":

            if "error" not in result:
                items.append({
                    "source_type": "market_data",
                    "title": f"{result.get('ticker')} price movement",
                    "ticker": result.get("ticker"),
                    "change_percent": result.get("change_percent"),
                    "published_at": None,
                    "url": None,
                    "relevance": 1.0,
                })

        elif tool == "search_recent_company_news":

            for article in result.get("results", []):

                domain = (article.get("source") or "").lower()
                source_type = (
                    "major_news"
                    if any(d in domain for d in MAJOR_NEWS_DOMAINS)
                    else "general_news"
                )

                items.append({
                    "source_type": source_type,
                    "title": article.get("title"),
                    "published_at": article.get("published_at"),
                    "url": article.get("url"),
                    "relevance": 0.7,
                    "text": article.get("summary"),
                })

    return items


def merge_evidence(
    internal_documents: list,
    market_data: list,
    external_news: list,
) -> dict:

    return {

        "internal_documents":
            internal_documents,

        "market_data":
            market_data,

        "external_news":
            external_news,

    }
