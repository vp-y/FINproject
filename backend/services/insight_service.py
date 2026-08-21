from database.connection import SessionLocal
from services.portfolio_service import get_holdings
from services.risk_service import analyze_portfolio_concentration
from rag.retriever import retrieve
from rag.generator import generate_answer_with_sources

# Maps holding tickers to the company name used as the `company` field
# in rag/indexer.py's metadata, so RAG search can filter to the right
# document. Only covers companies we've actually indexed documents for.
TICKER_TO_COMPANY = {
    "AAPL": "Apple",
    "NVDA": "NVIDIA"
}


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

            company = TICKER_TO_COMPANY.get(ticker)

            if not company:
                # we don't have indexed documents for this ticker yet
                continue

            chunks = retrieve(
                f"{company} risk factors",
                company=company,
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
