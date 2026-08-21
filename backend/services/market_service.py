import yfinance as yf


def get_stock_price(
    ticker: str
):

    stock = yf.Ticker(
        ticker
    )

    data = stock.history(
        period="1d"
    )

    price = data["Close"].iloc[-1]

    return {
        "ticker": ticker,
        "price": float(price)
    }


def get_historical_returns(
    ticker: str,
    period: str = "1y"
):
    """Daily percentage returns for a ticker over the given period,
    as a pandas Series indexed by date."""

    stock = yf.Ticker(
        ticker
    )

    history = stock.history(
        period=period
    )

    return history["Close"].pct_change().dropna()
