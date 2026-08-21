from external.web_search import (
    ExternalSearchService,
    TavilyProvider,
)
from external.news_service import normalize_tavily_results


def search_recent_company_news(
    ticker: str,
    query: str,
) -> dict:
    """
    Search recent external information about
    a company.

    Use this only when recent events or news
    may explain a portfolio or market change.

    Args:
        ticker: Company ticker.
        query: Targeted search query.

    Returns:
        Recent external evidence.
    """

    search_service = ExternalSearchService(
        provider=TavilyProvider()
    )

    results = search_service.search(
        query=query,
        max_results=5,
    )

    return {
        "ticker": ticker,
        "results": normalize_tavily_results(results),
    }
