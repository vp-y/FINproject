def normalize_article(
    title: str,
    source: str,
    published_at: str,
    url: str,
    summary: str,
) -> dict:

    return {
        "title": title,
        "source": source,
        "published_at": published_at,
        "url": url,
        "summary": summary,
    }


def normalize_tavily_results(results: list[dict]) -> list[dict]:
    """Maps Tavily's raw result shape into normalize_article()'s format
    so the rest of the platform never has to know which provider
    produced it. Tavily doesn't return a named source (e.g. "Reuters"),
    only a URL, so one is derived from the domain instead of invented.
    published_date isn't guaranteed present on every query type, so it
    falls back to an empty string rather than assuming it's there."""

    normalized = []

    for result in results:

        url = result.get("url", "")

        try:
            source = url.split("/")[2] if url else "unknown"
        except IndexError:
            source = "unknown"

        normalized.append(
            normalize_article(
                title=result.get("title", ""),
                source=source,
                published_at=result.get("published_date", ""),
                url=url,
                summary=result.get("content", ""),
            )
        )

    return normalized
