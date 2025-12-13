"""
Database utility functions for the API layer.

This module provides helper functions to query the PostgreSQL database
for sentiment data. It wraps the existing SQLConnection class and provides
high-level functions for common queries.

Usage:
    from db import get_sentiment_by_ticker, get_sentiment_trends

    # Get all sentiment data for a specific ticker
    data = get_sentiment_by_ticker('AAPL')

    # Get sentiment trends over time
    trends = get_sentiment_trends(days=30)
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional

import psycopg2
import psycopg2.extras
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from db.connection import SQLConnection

load_dotenv('/Users/fastcheetah/PycharmProjects/MarketSent/.env')
db_connection_str = os.getenv("DB_CONNECTION_STRING")
engine = create_engine(db_connection_str)


def get_db_connection():
    """
    Create and return a new database connection.

    Example:
        with get_db_connection() as db:
            db.cursor.execute("SELECT * FROM posts")
    """

    return SQLConnection()


def get_all_posts(limit: int = 1000) -> list[dict]:
    """
    Fetch all posts with pagination.

    Args:
        limit: Maximum number of posts to return (default 1000)

    Returns:
        List of post dictionaries with sentiment data
    """

    try:
        with get_db_connection() as db:
            cursor = db.cursor(cursor_factory=RealDictCursor)

            query = """SELECT * 
                       FROM posts
                       ORDER BY creation DESC
                       LIMIT %s """

            cursor.execute(query, (limit))

            posts = cursor.fetchall()

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

    return posts


def get_sentiment_by_ticker(ticker: str, days: int) -> list[dict]:
    """
    Get all posts mentioning a specific ticker symbol.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        days: Optional number of days to look back (None = all time)

    Returns:
        List of post dictionaries containing the ticker

    """

    try:
        with get_db_connection() as db:
            cursor = db.conn.cursor(cursor_factory=RealDictCursor)

            if days is None:
                days = 7
            if ticker is None:
                raise NameError

            date_limit = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


            query = """SELECT *
                    FROM posts
                    WHERE UPPER(%s) = ANY(SELECT UPPER(t) FROM unnest(tickers::text[]) AS t)
                      AND creation BETWEEN %s AND CURRENT_TIMESTAMP
                    """

            cursor.execute(query, (ticker, date_limit))
            posts = cursor.fetchall()
            print(f"Results found: {len(posts)}")

    except NameError as e:
        print(f"No ticker given")
        return []

    except Exception as e:
        print(f"Database error: {e}")
        return []

    return posts


def get_sentiment_trends(days: int = 7, ticker: Optional[str] = None) -> list[dict]:
    """
    Get daily aggregated sentiment trends.

    Args:
        days: Number of days to look back (default 30)
        ticker: Optional ticker to filter by

    Returns:
        List of daily sentiment averages:
        [
            {
                'date': '2024-01-15',
                'avg_positive': 0.45,
                'avg_negative': 0.25,
                'avg_neutral': 0.30,
                'post_count': 42
            },
            ...
        ]
    """

    try:
        with get_db_connection() as db:
            cursor = db.conn.cursor()

            date_limit = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            if ticker is None:
                query = """
                    SELECT creation AS date,
                           AVG(positive) AS avg_positive,
                           AVG(negative) AS avg_negative,
                           AVG(neutral) AS avg_neutral,
                           COUNT(*) AS post_count
                    FROM posts
                    WHERE creation BETWEEN %s AND CURRENT_TIMESTAMP
                    GROUP BY creation
                    ORDER BY creation
                """
                cursor.execute(query, (date_limit,))
            else:
                query = """
                    SELECT creation AS date,
                           AVG(positive) AS avg_positive,
                           AVG(negative) AS avg_negative,
                           AVG(neutral) AS avg_neutral,
                           COUNT(*) AS post_count
                    FROM posts
                    WHERE UPPER(%s) = ANY(SELECT UPPER(t) FROM unnest(tickers::text[]) AS t)
                      AND creation BETWEEN %s AND CURRENT_TIMESTAMP
                    GROUP BY creation
                    ORDER BY creation
                """
                cursor.execute(query, (ticker, date_limit))

            return cursor.fetchall()

    except Exception as e:
        print(f"Database error: {e}")
        return []


def get_top_ticker_list(days: int = 7) -> list[dict]:
    """
    Get the most frequently mentioned tickers.

    Args:
        days: Number of days to look back (default 7)

    Returns:
        List of ticker dictionaries with mention counts and avg sentiment:
        [
            {
                'ticker': 'TSLA',
                'mention_count': 150,
                'avg_positive': 0.52,
                'avg_negative': 0.18,
                'avg_neutral': 0.30
            },
            ...
        ]
    """

    try:
        with get_db_connection() as db:
            cursor = db.conn.cursor()
            date_limit = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            query = """
                    SELECT UPPER(TRIM(BOTH '{}' FROM TRIM(ticker))),       
                           COUNT(*)     AS mention_count,
                           AVG(positive) AS avg_positive,
                           AVG(negative) AS avg_negative,
                           AVG(neutral) AS avg_neutral
                    FROM posts,
                         LATERAL unnest(string_to_array(tickers, ',')) AS ticker
                    WHERE creation >= %s
                      AND tickers IS NOT NULL
                      AND tickers != ''
                    GROUP BY UPPER(TRIM(BOTH '{}' FROM TRIM(ticker)))
                    ORDER BY mention_count DESC
                    """
            cursor.execute(query, (date_limit,))

            return cursor.fetchall()
    except Exception as e:
        print(f"Database error: {e}")
        return []


def get_ticker_sentiment_over_time(ticker: str, days: int = 30) -> list[dict]:
    """
    Get daily sentiment for a specific ticker over time.

    Args:
        ticker: Stock ticker symbol
        days: Number of days to look back

    Returns:
        List of daily sentiment data for the ticker:
        [
            {
                'date': '2024-01-15',
                'positive': 0.55,
                'negative': 0.15,
                'neutral': 0.30,
                'post_count': 12,
                'avg_score': 156.5  # Reddit score
            },
            ...
        ]

    TODO:
        - Filter posts containing the ticker
        - Group by date
    """

    try:
        with get_db_connection() as db:
            cursor = db.conn.cursor(cursor_factory=RealDictCursor)
            date_limit = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            query = """
                SELECT
                    creation AS date,
                    AVG(positive) AS avg_positive,
                    AVG(negative) AS avg_negative,
                    AVG(neutral) AS avg_neutral,
                    COUNT(*) AS post_count,
                    AVG(score) AS avg_score
                FROM posts
                WHERE UPPER(%s) = ANY(SELECT UPPER(t) FROM unnest(tickers::text[]) AS t)
                  AND creation BETWEEN %s AND CURRENT_TIMESTAMP
                GROUP BY creation
                ORDER BY creation
            """
            cursor.execute(query, (ticker, date_limit))
            return cursor.fetchall()

    except Exception as e:
        print(f"Database error: {e}")
        return []


