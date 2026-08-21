import yfinance as yf


def get_market_context(
    ticker: str,
    period: str = "5d",
) -> dict:
    """
    Retrieve recent market movement for a ticker.

    Returns recent prices and percentage change.
    """

    stock = yf.Ticker(ticker)

    history = stock.history(
        period=period
    )

    if history.empty:

        return {
            "ticker": ticker,
            "error": "No market data found",
        }

    start_price = float(
        history["Close"].iloc[0]
    )

    latest_price = float(
        history["Close"].iloc[-1]
    )

    change_percent = (
        (latest_price - start_price)
        / start_price
    ) * 100

    return {
        "ticker": ticker,
        "period": period,
        "start_price": start_price,
        "latest_price": latest_price,
        "change_percent": change_percent,
    }
