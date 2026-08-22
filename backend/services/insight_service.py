from database.connection import SessionLocal
from services.portfolio_service import get_holdings
from services.risk_service import analyze_portfolio_concentration
from rag.retriever import retrieve
from rag.generator import generate_answer_with_sources
from data_pipeline.company_mapper import get_company_details

# Previously a hardcoded {"AAPL": "Apple", "NVDA": "NVIDIA"} dict — every
# ticker onboarded after the original two seeded holdings (see
# data_pipeline/pipeline.py) would silently fall through it and never
# get RAG search results. Replaced with a live yfinance lookup so this
# scales to any ticker, and with retrieve(ticker=...) below (an exact
# identifier match on the `ticker` metadata field rag/indexer.py now
# attaches) rather than a fuzzy company-name match.


def explain_portfolio_risk(portfolio_id):
    """
    The Step 2.13 workflow:
    Portfolio API -> Risk Engine -> find risky companies
        -> RAG search -> retrieve reports -> generate explanation
    """

    db = SessionLocal()

    try:
        holdings = get_holdings(db, portfolio_id)

        if not holdings:
            return {
                "error": f"No holdings found for portfolio {portfolio_id}."
            }

        concentration = analyze_portfolio_concentration(holdings)

        risky_tickers = concentration["riskiest_companies"]

        retrieved_chunks = []

        for ticker in risky_tickers:

            company_name = get_company_details(ticker).get("name") or ticker

            chunks = retrieve(
                f"{company_name} risk factors",
                ticker=ticker,
                top_k=3
            )

            retrieved_chunks.extend(chunks)

        weights_summary = ", ".join(
            f"{p['ticker']} {p['weight'] * 100:.0f}%"
            for p in concentration["positions"]
        )

        question = (
            f"My portfolio holds: {weights_summary}. "
            f"{concentration['top_sector']} makes up "
            f"{concentration['top_sector_weight'] * 100:.0f}% of the "
            f"portfolio. Why is my portfolio risky?"
        )

        if retrieved_chunks:
            generation = generate_answer_with_sources(
                question,
                retrieved_chunks
            )
        else:
            # no indexed documents available for the risky companies —
            # fall back to a concentration-only explanation instead of
            # silently returning nothing
            generation = {
                "answer": (
                    f"Portfolio risk is elevated because "
                    f"{concentration['top_sector_weight'] * 100:.0f}% is "
                    f"concentrated in {concentration['top_sector']} "
                    f"companies ({', '.join(risky_tickers)}). No indexed "
                    f"reports were available for these companies to cite "
                    f"specific risk factors."
                ),
                "sources": []
            }

        return {
            "portfolio_id": portfolio_id,
            "concentration": concentration,
            "answer": generation["answer"],
            "sources": generation["sources"]
        }

    finally:
        db.close()
