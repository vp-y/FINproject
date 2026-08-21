import re
import fitz
from bs4 import BeautifulSoup


def load_pdf(path):

    doc = fitz.open(path)

    text = ""

    for page in doc:
        text += page.get_text()

    return text


def load_pdf_pages(path):
    """Like load_pdf, but keeps page boundaries — needed for citations
    (page_number) since chunking a single flattened string loses track
    of which page any given chunk came from."""

    doc = fitz.open(path)

    pages = []

    for i, page in enumerate(doc, start=1):
        pages.append({
            "page": i,
            "text": page.get_text()
        })

    return pages


def load_html_pages(path):
    """For HTML documents (e.g. SEC EDGAR filings, which are the primary
    format for modern 10-Ks — not PDF). HTML has no real page concept, so
    the whole document is treated as a single page rather than fabricating
    page numbers that don't correspond to anything."""

    with open(path, "rb") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()

    for tag in soup.find_all(style=re.compile(r"display\s*:\s*none", re.I)):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)

    return [{
        "page": 1,
        "text": text
    }]


def load_document_pages(path):
    """Dispatches to the right loader based on file extension, so callers
    don't need to know whether a given document is a PDF or an HTML
    filing (the data_pipeline fetcher can produce either)."""

    ext = str(path).lower().rsplit(".", 1)[-1]

    if ext == "pdf":
        return load_pdf_pages(path)

    if ext in ("htm", "html"):
        return load_html_pages(path)

    raise ValueError(f"Unsupported document type: .{ext}")
