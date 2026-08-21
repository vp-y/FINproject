import yfinance as yf


def get_company_details(ticker):

    company = yf.Ticker(
        ticker
    )

    info = company.info

    return {
        "ticker": ticker,
        "name": info.get(
            "longName"
        ),
        "sector": info.get(
            "sector"
        ),
        "industry": info.get(
            "industry"
        )
    }
