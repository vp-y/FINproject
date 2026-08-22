import re

from data_pipeline.company_mapper import get_company_details
from data_pipeline.annual_report_fetcher import get_10k_url, download_report
from data_pipeline.document_manager import document_exists, get_document_path
from rag.ingest import ingest_document


def extract_filing_year(url):
    """SEC EDGAR primary document filenames encode the filing date as
    {ticker}-YYYYMMDD.htm — pull the year from it rather than leaving
    it blank, since it's already there for free."""

    match = re.search(r"-(\d{4})\d{4}\.\w+$", url)
    return int(match.group(1)) if match else None


def process_holding_row(holding, on_status=None):
    """Fetches (skipping if already on disk) and RAG-ingests one
    holding's most recent 10-K. `on_status(status, **fields)`, if given,
    is called at each state transition (fetching/indexing/indexed/
    failed/no_filing_found) so a caller can persist progress without
    this module knowing about the DB or WebSockets — used by
    services/onboarding_service.py; process_portfolio (below, used by
    the manual /data/sync endpoint) doesn't pass one and behaves exactly
    as it always has.

    Returns the same doc_entry dict process_portfolio has always
    returned ({"ticker","company","path","indexed","chunk_count"?/
    "index_error"?}), or None if no 10-K could be found at all —
    process_portfolio skips None entries, preserving its original
    "silently skip tickers with no filing" behavior.
    """

    def notify(status, **fields):
        if on_status:
            on_status(status, **fields)

    ticker = holding["ticker"]

    company = get_company_details(ticker)
    company_name = company["name"]

    print(
        "Processing:",
        company_name
    )

    newly_downloaded = False
    filing_year = None

    if document_exists(
        ticker
    ):

        path = get_document_path(ticker)
        print("  Already have report, skipping download.")
        notify(
            "indexed",
            company_name=company_name,
            document_path=path,
            chunk_count=None,
        )

    else:

        notify("fetching", company_name=company_name)

        url = get_10k_url(ticker)

        if not url:
            print(f"  No 10-K found on SEC EDGAR for {ticker}, skipping.")
            notify("no_filing_found", company_name=company_name)
            return None

        print("  Downloading annual report...")

        path = download_report(
            ticker,
            company_name,
            url
        )

        filing_year = extract_filing_year(url)
        newly_downloaded = True

    doc_entry = {
        "ticker": ticker,
        "company": company_name,
        "path": path,
        "indexed": False
    }

    if newly_downloaded:

        notify("indexing", company_name=company_name, document_path=path)

        # Automatically trigger RAG ingestion right after download —
        # wrapped so a failure here (e.g. embedding API quota) still
        # leaves the download itself intact instead of losing it.
        try:
            print("  Indexing into RAG pipeline...")

            chunk_count = ingest_document(
                path,
                document_name=f"{company_name} Annual Report",
                company=company_name,
                document_type="Annual Report",
                year=filing_year,
                ticker=ticker,
            )

            doc_entry["indexed"] = True
            doc_entry["chunk_count"] = chunk_count

            notify(
                "indexed",
                company_name=company_name,
                document_path=path,
                chunk_count=chunk_count,
            )

        except Exception as e:
            print(f"  RAG ingestion failed ({e.__class__.__name__}): {e}")
            doc_entry["index_error"] = str(e)
            notify("failed", company_name=company_name, error=str(e))

    return doc_entry


def process_portfolio(
    holdings
):

    documents = []

    for stock in holdings:

        doc_entry = process_holding_row(stock)

        if doc_entry is not None:
            documents.append(doc_entry)

    return documents
