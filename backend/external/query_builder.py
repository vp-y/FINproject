def build_company_news_query(
    ticker: str,
    company_name: str | None = None,
) -> str:

    identifier = (
        company_name
        if company_name
        else ticker
    )

    return (
        f"{identifier} {ticker} "
        "stock earnings risk news"
    )


def build_event_query(
    ticker: str,
    event_type: str,
) -> str:

    return (
        f"{ticker} "
        f"{event_type} "
        "latest news"
    )
