import os
from pathlib import Path

import requests
from data_pipeline.stock_mapper import mapper as _mapper

# data/documents/ lives at the project root, not under backend/ — anchor
# to this file's location so it resolves correctly regardless of the
# process's current working directory.
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "documents"

# SEC requires a descriptive User-Agent identifying the requester
# (https://www.sec.gov/os/webmaster-faq#developers) — generic/missing
# User-Agents get rate-limited or blocked.
SEC_HEADERS = {
    "User-Agent": "Aegis Research Project research@aegis.local"
}


def get_10k_url(ticker):
    """Look up the URL of a company's most recent 10-K filing via the
    real SEC EDGAR API (ticker -> CIK -> submissions -> latest 10-K)."""

    cik = _mapper.ticker_to_cik.get(ticker.upper())

    if not cik:
        return None

    submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"

    response = requests.get(
        submissions_url,
        headers=SEC_HEADERS
    )
    response.raise_for_status()

    filings = response.json()["filings"]["recent"]

    for i, form in enumerate(filings["form"]):

        if form == "10-K":

            accession = filings["accessionNumber"][i].replace("-", "")
            primary_doc = filings["primaryDocument"][i]
            cik_no_leading_zeros = str(int(cik))

            return (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{cik_no_leading_zeros}/{accession}/{primary_doc}"
            )

    return None


def download_report(
    ticker,
    company_name,
    url
):

    folder = DATA_DIR / ticker

    os.makedirs(
        folder,
        exist_ok=True
    )

    # SEC's modern 10-K filings are HTML, not PDF — save with the real
    # extension from the source URL instead of forcing .pdf, which would
    # silently produce a file the PDF loader can't parse.
    ext = os.path.splitext(url)[1] or ".htm"
    file_path = folder / f"annual_report{ext}"

    response = requests.get(
        url,
        headers=SEC_HEADERS
    )

    with open(
        file_path,
        "wb"
    ) as f:

        f.write(
            response.content
        )

    return str(file_path)
