"""Ticker extraction shared by database and snapshot ingestion."""

import re
from typing import Optional

from src.pipeline.CompanyTickers import COMPANY_TICKERS


KNOWN_TICKERS = frozenset(COMPANY_TICKERS.values())
TICKER_PATTERN = re.compile(
    r"(?<![A-Z0-9])(\$?)([A-Z]{1,5}(?:\.[A-Z]{1,3})?)(?![A-Z0-9])"
)
FALSE_POSITIVES = frozenset({"AI", "CEO", "ETF", "GDP", "IPO", "LOL", "USA", "YOLO"})
AMBIGUOUS_COMPANY_ALIASES = frozenset(
    {"block", "ford", "ge", "meta", "shell", "snap", "square", "target", "zoom"}
)


def extract_tickers(value: Optional[str]) -> Optional[str]:
    """Extract supported cashtags, ticker symbols, and company aliases."""

    if not value:
        return None

    found: list[str] = []

    def add(symbol: str) -> None:
        if symbol not in FALSE_POSITIVES and symbol not in found:
            found.append(symbol)

    for match in TICKER_PATTERN.finditer(value):
        cashtag, candidate = match.groups()
        if candidate in KNOWN_TICKERS and (cashtag or len(candidate) > 1):
            add(candidate)

    for company, ticker in sorted(
        COMPANY_TICKERS.items(), key=lambda item: len(item[0]), reverse=True
    ):
        company_pattern = r"(?<!\w)" + re.escape(company).replace(r"\ ", r"\s+") + r"(?!\w)"
        match = re.search(company_pattern, value, flags=re.IGNORECASE)
        if match and not (
            company in AMBIGUOUS_COMPANY_ALIASES and match.group(0).islower()
        ):
            add(ticker)

    return ",".join(found) if found else None
