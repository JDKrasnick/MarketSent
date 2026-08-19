"""Database queries used by the MarketSent API."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from psycopg2.extras import RealDictCursor

from db.connection import SQLConnection


logger = logging.getLogger(__name__)


class DatabaseQueryError(RuntimeError):
    """Raised when the API cannot complete a database query."""


def get_db_connection() -> SQLConnection:
    """Return a context-managed PostgreSQL connection."""

    return SQLConnection()


def _date_limit(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


def _raise_query_error(operation: str, error: Exception) -> None:
    logger.exception("Database operation failed: %s", operation)
    raise DatabaseQueryError(f"Unable to {operation}") from error


def get_all_posts(limit: int = 1000) -> list[dict]:
    """Fetch the most recent posts."""

    try:
        with get_db_connection() as db:
            cursor = db.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT *
                FROM posts
                ORDER BY creation DESC, postid DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cursor.fetchall()
    except Exception as error:
        _raise_query_error("fetch posts", error)


def search_posts(query: str, limit: int = 50) -> list[dict]:
    """Search post titles and bodies, newest first."""

    try:
        with get_db_connection() as db:
            cursor = db.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT *
                FROM posts
                WHERE text ILIKE %s OR COALESCE(post_text, '') ILIKE %s
                ORDER BY creation DESC, postid DESC
                LIMIT %s
                """,
                (f"%{query}%", f"%{query}%", limit),
            )
            return cursor.fetchall()
    except Exception as error:
        _raise_query_error("search posts", error)


def get_sentiment_by_ticker(ticker: str, days: int = 7) -> list[dict]:
    """Return recent posts that mention a ticker."""

    try:
        with get_db_connection() as db:
            cursor = db.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT *
                FROM posts
                WHERE EXISTS (
                    SELECT 1
                    FROM unnest(
                        string_to_array(
                            TRIM(BOTH '{}' FROM COALESCE(tickers, '')),
                            ','
                        )
                    ) AS value
                    WHERE UPPER(TRIM(value)) = UPPER(%s)
                )
                  AND creation >= %s
                ORDER BY creation DESC, score DESC
                """,
                (ticker, _date_limit(days)),
            )
            return cursor.fetchall()
    except Exception as error:
        _raise_query_error("fetch ticker posts", error)


def get_sentiment_trends(days: int = 7, ticker: Optional[str] = None) -> list[dict]:
    """Return daily sentiment averages, optionally filtered by ticker."""

    try:
        with get_db_connection() as db:
            cursor = db.conn.cursor(cursor_factory=RealDictCursor)
            parameters: list[object] = [_date_limit(days)]
            ticker_filter = ""

            if ticker:
                ticker_filter = """
                    AND EXISTS (
                        SELECT 1
                        FROM unnest(
                            string_to_array(
                                TRIM(BOTH '{}' FROM COALESCE(tickers, '')),
                                ','
                            )
                        ) AS value
                        WHERE UPPER(TRIM(value)) = UPPER(%s)
                    )
                """
                parameters.append(ticker)

            cursor.execute(
                f"""
                SELECT creation AS date,
                       AVG(positive) AS avg_positive,
                       AVG(negative) AS avg_negative,
                       AVG(neutral) AS avg_neutral,
                       COUNT(*) AS post_count
                FROM posts
                WHERE creation >= %s
                  {ticker_filter}
                GROUP BY creation
                ORDER BY creation
                """,
                tuple(parameters),
            )
            return cursor.fetchall()
    except Exception as error:
        _raise_query_error("fetch sentiment trends", error)


def _get_ranked_tickers(days: int, limit: int, hot: bool) -> list[tuple]:
    order_by = (
        "mention_count * (1 + GREATEST(AVG(positive) - AVG(negative), 0)) DESC, "
        "mention_count DESC"
        if hot
        else "mention_count DESC"
    )

    try:
        with get_db_connection() as db:
            cursor = db.conn.cursor()
            cursor.execute(
                f"""
                SELECT UPPER(TRIM(ticker.value)) AS symbol,
                       COUNT(*) AS mention_count,
                       AVG(positive) AS avg_positive,
                       AVG(negative) AS avg_negative,
                       AVG(neutral) AS avg_neutral
                FROM posts
                CROSS JOIN LATERAL unnest(
                    string_to_array(
                        TRIM(BOTH '{{}}' FROM COALESCE(posts.tickers, '')),
                        ','
                    )
                ) AS ticker(value)
                WHERE creation >= %s
                  AND TRIM(ticker.value) != ''
                GROUP BY UPPER(TRIM(ticker.value))
                ORDER BY {order_by}
                LIMIT %s
                """,
                (_date_limit(days), limit),
            )
            return cursor.fetchall()
    except Exception as error:
        operation = "fetch hot tickers" if hot else "fetch top tickers"
        _raise_query_error(operation, error)


def get_top_ticker_list(days: int = 7, limit: int = 10) -> list[tuple]:
    """Return tickers ranked by mention count."""

    return _get_ranked_tickers(days, limit, hot=False)


def get_hot_ticker_list(days: int = 7, limit: int = 10) -> list[tuple]:
    """Return tickers ranked by mentions with a positive-sentiment boost."""

    return _get_ranked_tickers(days, limit, hot=True)


def get_ticker_sentiment_over_time(ticker: str, days: int = 30) -> list[dict]:
    """Return daily ticker sentiment with average Reddit score."""

    try:
        with get_db_connection() as db:
            cursor = db.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT creation AS date,
                       AVG(positive) AS avg_positive,
                       AVG(negative) AS avg_negative,
                       AVG(neutral) AS avg_neutral,
                       COUNT(*) AS post_count,
                       AVG(score) AS avg_score
                FROM posts
                WHERE EXISTS (
                    SELECT 1
                    FROM unnest(
                        string_to_array(
                            TRIM(BOTH '{}' FROM COALESCE(tickers, '')),
                            ','
                        )
                    ) AS value
                    WHERE UPPER(TRIM(value)) = UPPER(%s)
                )
                  AND creation >= %s
                GROUP BY creation
                ORDER BY creation
                """,
                (ticker, _date_limit(days)),
            )
            return cursor.fetchall()
    except Exception as error:
        _raise_query_error("fetch ticker sentiment history", error)


def get_posts_time(period: str, limit: int = 100) -> list[dict]:
    """Return recent posts from the requested day or week window."""

    days = 1 if period == "day" else 7
    try:
        with get_db_connection() as db:
            cursor = db.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT *
                FROM posts
                WHERE creation >= %s
                ORDER BY creation DESC, score DESC
                LIMIT %s
                """,
                (_date_limit(days), limit),
            )
            return cursor.fetchall()
    except Exception as error:
        _raise_query_error("fetch recent posts", error)
