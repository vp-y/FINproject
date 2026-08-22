from sec_cik_mapper import StockMapper

# Instantiated once here (building the full ticker<->CIK<->company-name
# table takes a moment) and imported everywhere else that needs it —
# annual_report_fetcher.py (ticker -> CIK) and ticker_resolver.py
# (company name -> ticker) — rather than each constructing its own copy.
mapper = StockMapper()
