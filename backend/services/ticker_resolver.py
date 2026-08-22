import re
from difflib import get_close_matches, SequenceMatcher

from data_pipeline.stock_mapper import mapper

# Built once at import from sec_cik_mapper's full ticker universe — no
# paid symbol-search API needed.
_TICKER_TO_NAME: dict[str, str] = mapper.ticker_to_company_name

# SEC company names carry corporate-form suffixes ("Apple Inc.",
# "Microsoft Corp", "Jpmorgan Chase & Co", "Amazon Com Inc") that a user
# typing a plain company name ("apple", "microsoft") never includes.
# Comparing raw strings tanks SequenceMatcher's ratio() for exactly the
# common, unambiguous case — stripping these first is what makes "apple"
# resolve as cleanly as "AAPL" itself.
_SUFFIX_WORDS = (
    r"inc|incorporated|corp|corporation|co|company|ltd|limited|llc|plc|"
    r"group|holdings?|com|the|class\s*[a-z]"
)
_SUFFIX_PATTERN = re.compile(rf"\b(?:{_SUFFIX_WORDS})\b", re.IGNORECASE)
_PUNCT_PATTERN = re.compile(r"[^\w\s]")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def _normalize_name(name: str) -> str:
    name = _PUNCT_PATTERN.sub(" ", name.lower())
    name = _SUFFIX_PATTERN.sub(" ", name)
    return _WHITESPACE_PATTERN.sub(" ", name).strip()


# normalized name -> ticker. Multiple tickers can normalize to the same
# stripped name — e.g. AMJB and JPM are both literally "Jpmorgan Chase &
# Co" in SEC's data (a secondary listing/share class sharing the parent
# entity's legal name). When that happens, prefer the shortest ticker
# symbol: primary common-stock tickers (JPM) are reliably shorter than
# the preferred-share/fund variants (AMJB) that share a big issuer's
# name — a cheap, no-dependency proxy for "the one a user means".
_normalized_candidates: dict[str, list[str]] = {}
for _ticker, _name in _TICKER_TO_NAME.items():
    _normalized = _normalize_name(_name)
    if _normalized:
        _normalized_candidates.setdefault(_normalized, []).append(_ticker)

_NORMALIZED_TO_TICKER: dict[str, str] = {
    name: min(tickers, key=lambda t: (len(t), t))
    for name, tickers in _normalized_candidates.items()
}

_ALL_NORMALIZED_NAMES: list[str] = list(_NORMALIZED_TO_TICKER.keys())

# Below this confidence, don't silently write the guess — surface it to
# the caller as "ambiguous" so a human can confirm/pick an alternative.
MATCH_CONFIDENCE_THRESHOLD = 0.85
# A containment match (input is a whole-word prefix of the candidate,
# e.g. "tesla" -> "tesla motors" normalized from "Tesla, Inc.") is a
# near-certain match even though raw string-similarity ratio is low.
CONTAINMENT_CONFIDENCE = 0.95


def _candidate(ticker: str, name: str, confidence: float) -> dict:
    return {
        "ticker": ticker,
        "name": name,
        "confidence": round(confidence, 4),
    }


def resolve_ticker(raw_input: str) -> dict:
    """
    Resolve free text (a ticker or a company name, typed by a user who
    may not know the exact ticker) to a real ticker symbol.

    Match order: exact ticker -> exact normalized-name (suffixes like
    "Inc"/"Corp" stripped) -> normalized prefix/containment -> fuzzy
    fallback (difflib.get_close_matches over normalized names).

    Returns:
        {
            "input": the original raw_input,
            "ticker": resolved ticker or None,
            "matched_name": the matched company name or None,
            "confidence": float in [0, 1],
            "status": "matched" | "ambiguous" | "not_found",
            "alternatives": [{"ticker","name","confidence"}...] — populated
                for "ambiguous" so the caller can offer a pick-list.
        }
    """

    cleaned = raw_input.strip()

    if not cleaned:
        return {
            "input": raw_input,
            "ticker": None,
            "matched_name": None,
            "confidence": 0.0,
            "status": "not_found",
            "alternatives": [],
        }

    upper = cleaned.upper()

    if upper in _TICKER_TO_NAME:
        return {
            "input": raw_input,
            "ticker": upper,
            "matched_name": _TICKER_TO_NAME[upper],
            "confidence": 1.0,
            "status": "matched",
            "alternatives": [],
        }

    normalized_input = _normalize_name(cleaned)

    if not normalized_input:
        return {
            "input": raw_input,
            "ticker": None,
            "matched_name": None,
            "confidence": 0.0,
            "status": "not_found",
            "alternatives": [],
        }

    if normalized_input in _NORMALIZED_TO_TICKER:
        ticker = _NORMALIZED_TO_TICKER[normalized_input]
        return {
            "input": raw_input,
            "ticker": ticker,
            "matched_name": _TICKER_TO_NAME[ticker],
            "confidence": 1.0,
            "status": "matched",
            "alternatives": [],
        }

    # Whole-word prefix containment, e.g. normalized "tesla" is a prefix
    # of normalized "tesla motors" (from "Tesla, Inc." once suffix-
    # stripped is a no-op here — "motors" isn't a suffix word, so the
    # candidate name legitimately stays "tesla motors" if that's what
    # the filer used; the common case is exact after stripping, this
    # branch covers the shorter-input variant).
    containment_candidates = [
        _candidate(
            _NORMALIZED_TO_TICKER[name],
            _TICKER_TO_NAME[_NORMALIZED_TO_TICKER[name]],
            CONTAINMENT_CONFIDENCE,
        )
        for name in _ALL_NORMALIZED_NAMES
        if name.startswith(normalized_input + " ") or name == normalized_input
    ]

    # Fused-name fallback, e.g. "exxon" -> "exxonmobil" ("Exxonmobil
    # Holdings Corp" has no space after "exxon"). SequenceMatcher.ratio()
    # alone would lose this to an unrelated but proportionally-closer
    # short name (e.g. "Texxon Holding Ltd" vs "exxon"), since ratio()
    # rewards short overlap-heavy strings over an exact-but-longer
    # prefix match — plain str.startswith doesn't have that bias.
    # Gated to len >= 4 to avoid short/generic inputs matching noise.
    if not containment_candidates and len(normalized_input) >= 4:
        containment_candidates = [
            _candidate(
                _NORMALIZED_TO_TICKER[name],
                _TICKER_TO_NAME[_NORMALIZED_TO_TICKER[name]],
                CONTAINMENT_CONFIDENCE - 0.05,
            )
            for name in _ALL_NORMALIZED_NAMES
            if name.startswith(normalized_input) and name != normalized_input
        ]

    if containment_candidates:
        # Prefer the shortest candidate name — the closest match to what
        # the user actually typed, not an unrelated longer name that
        # happens to start the same way.
        containment_candidates.sort(key=lambda c: len(c["name"]))
        best = containment_candidates[0]
        return {
            "input": raw_input,
            "ticker": best["ticker"],
            "matched_name": best["name"],
            "confidence": best["confidence"],
            "status": "matched",
            "alternatives": containment_candidates[1:],
        }

    close_names = get_close_matches(
        normalized_input,
        _ALL_NORMALIZED_NAMES,
        n=5,
        cutoff=0.5,
    )

    if not close_names:
        return {
            "input": raw_input,
            "ticker": None,
            "matched_name": None,
            "confidence": 0.0,
            "status": "not_found",
            "alternatives": [],
        }

    candidates = [
        _candidate(
            _NORMALIZED_TO_TICKER[name],
            _TICKER_TO_NAME[_NORMALIZED_TO_TICKER[name]],
            SequenceMatcher(None, normalized_input, name).ratio(),
        )
        for name in close_names
    ]

    candidates.sort(key=lambda c: c["confidence"], reverse=True)

    best = candidates[0]

    if best["confidence"] >= MATCH_CONFIDENCE_THRESHOLD:
        return {
            "input": raw_input,
            "ticker": best["ticker"],
            "matched_name": best["name"],
            "confidence": best["confidence"],
            "status": "matched",
            "alternatives": candidates[1:],
        }

    return {
        "input": raw_input,
        "ticker": None,
        "matched_name": None,
        "confidence": best["confidence"],
        "status": "ambiguous",
        "alternatives": candidates,
    }


def resolve_holdings_input(rows: list[dict]) -> list[dict]:
    """
    Batch helper for onboarding. Attaches resolve_ticker(row["input"])
    onto each row under row["resolution"]. Pure in-memory — the SEC
    ticker table is already fully loaded by `mapper`, no network call.
    """

    return [
        {**row, "resolution": resolve_ticker(row["input"])}
        for row in rows
    ]
