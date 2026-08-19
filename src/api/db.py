"""Portable database queries used by the MarketSent API."""

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text

from db.connection import get_backend, get_engine


logger = logging.getLogger(__name__)


class DatabaseQueryError(RuntimeError):
    """Raised when the API cannot complete a database query."""


def _date_limit(days: int):
    return datetime.now(timezone.utc).date() - timedelta(days=days)


def _raise_query_error(operation: str, error: Exception) -> None:
    logger.exception("Database operation failed: %s", operation)
    raise DatabaseQueryError(f"Unable to {operation}") from error


def _mapping_rows(statement: str, parameters: Optional[dict] = None) -> list[dict]:
    with get_engine().connect() as connection:
        result = connection.execute(text(statement), parameters or {})
        return [dict(row) for row in result.mappings()]


def check_database() -> str:
    """Verify storage and return the active backend."""

    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))
    return get_backend()


def get_all_posts(limit: int = 1000) -> list[dict]:
    """Fetch the most recent posts."""

    try:
        return _mapping_rows(
            """
            SELECT * FROM posts
            ORDER BY creation DESC, postid DESC
            LIMIT :limit
            """,
            {"limit": limit},
        )
    except Exception as error:
        _raise_query_error("fetch posts", error)


def search_posts(query: str, limit: int = 50) -> list[dict]:
    """Search post titles and bodies, newest first."""

    try:
        return _mapping_rows(
            """
            SELECT * FROM posts
            WHERE LOWER(text) LIKE LOWER(:pattern)
               OR LOWER(COALESCE(post_text, '')) LIKE LOWER(:pattern)
            ORDER BY creation DESC, postid DESC
            LIMIT :limit
            """,
            {"pattern": f"%{query}%", "limit": limit},
        )
    except Exception as error:
        _raise_query_error("search posts", error)


TICKER_FILTER = """
(',' || UPPER(
    REPLACE(REPLACE(REPLACE(COALESCE(tickers, ''), ' ', ''), '{', ''), '}', '')
) || ',') LIKE :ticker_pattern
"""


def _ticker_pattern(ticker: str) -> str:
    return f"%,{ticker.strip().upper()},%"


def get_sentiment_by_ticker(ticker: str, days: int = 7) -> list[dict]:
    """Return recent posts that mention a ticker."""

    try:
        return _mapping_rows(
            f"""
            SELECT * FROM posts
            WHERE {TICKER_FILTER}
              AND creation >= :date_limit
            ORDER BY creation DESC, score DESC
            """,
            {"ticker_pattern": _ticker_pattern(ticker), "date_limit": _date_limit(days)},
        )
    except Exception as error:
        _raise_query_error("fetch ticker posts", error)


def get_sentiment_trends(days: int = 7, ticker: Optional[str] = None) -> list[dict]:
    """Return daily sentiment averages, optionally filtered by ticker."""

    parameters = {"date_limit": _date_limit(days)}
    ticker_filter = ""
    if ticker:
        ticker_filter = f"AND {TICKER_FILTER}"
        parameters["ticker_pattern"] = _ticker_pattern(ticker)

    try:
        return _mapping_rows(
            f"""
            SELECT creation AS date,
                   AVG(positive) AS avg_positive,
                   AVG(negative) AS avg_negative,
                   AVG(neutral) AS avg_neutral,
                   COUNT(*) AS post_count
            FROM posts
            WHERE creation >= :date_limit
              {ticker_filter}
            GROUP BY creation
            ORDER BY creation
            """,
            parameters,
        )
    except Exception as error:
        _raise_query_error("fetch sentiment trends", error)


def _split_tickers(value: Optional[str]) -> list[str]:
    normalized = (value or "").strip("{}").replace(" ", "")
    return [item.upper() for item in normalized.split(",") if item]


def _get_ranked_tickers(days: int, limit: int, hot: bool) -> list[tuple]:
    try:
        rows = _mapping_rows(
            """
            SELECT tickers, positive, negative, neutral
            FROM posts
            WHERE creation >= :date_limit
            """,
            {"date_limit": _date_limit(days)},
        )
    except Exception as error:
        operation = "fetch hot tickers" if hot else "fetch top tickers"
        _raise_query_error(operation, error)

    aggregates = defaultdict(lambda: {"count": 0, "positive": 0.0, "negative": 0.0, "neutral": 0.0})
    for row in rows:
        for ticker in set(_split_tickers(row.get("tickers"))):
            values = aggregates[ticker]
            values["count"] += 1
            for label in ("positive", "negative", "neutral"):
                values[label] += float(row.get(label) or 0)

    ranked = []
    for ticker, values in aggregates.items():
        count = values["count"]
        positive = values["positive"] / count
        negative = values["negative"] / count
        neutral = values["neutral"] / count
        hot_score = count * (1 + max(positive - negative, 0))
        ranked.append((ticker, count, positive, negative, neutral, hot_score))

    ranked.sort(key=lambda row: (row[5] if hot else row[1], row[1], row[0]), reverse=True)
    return [row[:5] for row in ranked[:limit]]


def get_top_ticker_list(days: int = 7, limit: int = 10) -> list[tuple]:
    return _get_ranked_tickers(days, limit, hot=False)


def get_hot_ticker_list(days: int = 7, limit: int = 10) -> list[tuple]:
    return _get_ranked_tickers(days, limit, hot=True)


def get_ticker_sentiment_over_time(ticker: str, days: int = 30) -> list[dict]:
    """Return daily ticker sentiment with average Reddit score."""

    try:
        return _mapping_rows(
            f"""
            SELECT creation AS date,
                   AVG(positive) AS avg_positive,
                   AVG(negative) AS avg_negative,
                   AVG(neutral) AS avg_neutral,
                   COUNT(*) AS post_count,
                   AVG(score) AS avg_score
            FROM posts
            WHERE {TICKER_FILTER}
              AND creation >= :date_limit
            GROUP BY creation
            ORDER BY creation
            """,
            {"ticker_pattern": _ticker_pattern(ticker), "date_limit": _date_limit(days)},
        )
    except Exception as error:
        _raise_query_error("fetch ticker sentiment history", error)


def get_posts_time(period: str, limit: int = 100) -> list[dict]:
    """Return recent posts from the requested day or week window."""

    days = 1 if period == "day" else 7
    try:
        return _mapping_rows(
            """
            SELECT * FROM posts
            WHERE creation >= :date_limit
            ORDER BY creation DESC, score DESC
            LIMIT :limit
            """,
            {"date_limit": _date_limit(days), "limit": limit},
        )
    except Exception as error:
        _raise_query_error("fetch recent posts", error)
