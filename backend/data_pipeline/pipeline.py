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


def process_portfolio(
    holdings
):

    documents = []

    for stock in holdings:

        ticker = stock["ticker"]

        company = get_company_details(
            ticker
        )

        print(
            "Processing:",
            company["name"]
        )

        newly_downloaded = False
        filing_year = None

        if document_exists(
            ticker
        ):

            path = get_document_path(ticker)
            print("  Already have report, skipping download.")

        else:

            url = get_10k_url(ticker)

            if not url:
                print(f"  No 10-K found on SEC EDGAR for {ticker}, skipping.")
                continue

            print("  Downloading annual report...")

            path = download_report(
                ticker,
                company["name"],
                url
            )

            filing_year = extract_filing_year(url)
            newly_downloaded = True

        doc_entry = {
            "ticker": ticker,
            "company": company["name"],
            "path": path,
            "indexed": False
        }

        if newly_downloaded:

            # Automatically trigger RAG ingestion right after download —
            # wrapped so a failure here (e.g. embedding API quota) still
            # leaves the download itself intact instead of losing it.
            try:
                print("  Indexing into RAG pipeline...")

                chunk_count = ingest_document(
                    path,
                    document_name=f"{company['name']} Annual Report",
                    company=company["name"],
                    document_type="Annual Report",
                    year=filing_year
                )

                doc_entry["indexed"] = True
                doc_entry["chunk_count"] = chunk_count

            except Exception as e:
                print(f"  RAG ingestion failed ({e.__class__.__name__}): {e}")
                doc_entry["index_error"] = str(e)

        documents.append(doc_entry)

    return documents
