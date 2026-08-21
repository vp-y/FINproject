import glob
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "documents"


def document_exists(
    ticker
):

    # The fetcher saves whatever extension the source document actually
    # has (.htm for modern SEC filings, .pdf for older ones) — checking
    # only for "annual_report.pdf" would never match a real SEC filing
    # and defeat the point of this check (every sync would re-download).
    matches = glob.glob(
        str(DATA_DIR / ticker / "annual_report.*")
    )

    return len(matches) > 0


def get_document_path(
    ticker
):

    matches = glob.glob(
        str(DATA_DIR / ticker / "annual_report.*")
    )

    return matches[0] if matches else None
