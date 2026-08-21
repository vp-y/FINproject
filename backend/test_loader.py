import sys
from rag.loader import load_pdf

sys.stdout.reconfigure(encoding="utf-8")

text = load_pdf(
    "../data/documents/AAPL_Annual_Report.pdf"
)

print(
    text[:1000]
)
