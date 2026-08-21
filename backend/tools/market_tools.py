from external.market_context import (
    get_market_context
)


def analyze_recent_market_move(
    ticker: str,
) -> dict:
    """
    Analyze recent market movement for a company.

    Use this when investigating recent portfolio
    changes or identifying significant price movements.

    Args:
        ticker: Stock ticker.

    Returns:
        Recent market context.
    """

    return get_market_context(
        ticker
    )
