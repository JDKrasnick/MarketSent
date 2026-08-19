"""HTTP routes for the MarketSent API."""

import os
import logging
import re
import secrets
import threading

from flask import Blueprint, jsonify, request

from src.api.db import (
    get_db_connection,
    get_hot_ticker_list,
    get_posts_time,
    get_sentiment_by_ticker,
    get_sentiment_trends,
    get_top_ticker_list,
    search_posts as search_posts_in_db,
)


api_bp = Blueprint("api", __name__)
logger = logging.getLogger(__name__)
_symbol_pattern = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")


def _integer_arg(name: str, default: int, minimum: int, maximum: int):
    raw_value = request.args.get(name)
    if raw_value is None:
        return default, None

    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return None, (jsonify({"error": f"{name} must be an integer"}), 400)

    if not minimum <= value <= maximum:
        return None, (
            jsonify({"error": f"{name} must be between {minimum} and {maximum}"}),
            400,
        )
    return value, None


def _normalized_symbol(symbol: str):
    normalized = symbol.strip().upper()
    if not _symbol_pattern.fullmatch(normalized):
        return None, (jsonify({"error": "Invalid ticker symbol"}), 400)
    return normalized, None


def _ticker_payload(rows: list[tuple]) -> list[dict]:
    return [
        {
            "symbol": row[0],
            "mentions": row[1],
            "sentiment": {
                "positive": round(float(row[2]), 4) if row[2] is not None else 0,
                "negative": round(float(row[3]), 4) if row[3] is not None else 0,
                "neutral": round(float(row[4]), 4) if row[4] is not None else 0,
            },
        }
        for row in rows
    ]


@api_bp.get("/posts")
def get_posts():
    period = request.args.get("time", "week").lower()
    if period not in {"day", "week"}:
        return jsonify({"error": "time must be either 'day' or 'week'"}), 400

    limit, error = _integer_arg("limit", 100, 1, 500)
    if error:
        return error

    posts = get_posts_time(period, limit)
    return jsonify({"posts": posts, "time": period, "count": len(posts)})


@api_bp.get("/posts/search")
def search_posts():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing required parameter: q"}), 400
    if len(query) > 200:
        return jsonify({"error": "q must be 200 characters or fewer"}), 400

    limit, error = _integer_arg("limit", 50, 1, 100)
    if error:
        return error

    results = search_posts_in_db(query, limit)
    return jsonify({"query": query, "results": results, "count": len(results)})


@api_bp.get("/toptickers")
def get_top_tickers():
    days, error = _integer_arg("days", 7, 1, 365)
    if error:
        return error
    limit, error = _integer_arg("limit", 10, 1, 100)
    if error:
        return error

    rows = get_top_ticker_list(days, limit)
    return jsonify({"tickers": _ticker_payload(rows), "days": days})


@api_bp.get("/hot_tickers")
def get_hot_tickers():
    days, error = _integer_arg("days", 7, 1, 365)
    if error:
        return error
    limit, error = _integer_arg("limit", 10, 1, 100)
    if error:
        return error

    rows = get_hot_ticker_list(days, limit)
    return jsonify({"tickers": _ticker_payload(rows), "days": days})


@api_bp.get("/tickers/<symbol>")
def get_ticker_sentiment(symbol: str):
    symbol, error = _normalized_symbol(symbol)
    if error:
        return error
    days, error = _integer_arg("days", 7, 1, 365)
    if error:
        return error

    posts = get_sentiment_by_ticker(symbol, days)
    return jsonify({"symbol": symbol, "days": days, "posts": posts})


@api_bp.get("/trends")
def get_ticker_sentiment_trends():
    days, error = _integer_arg("days", 7, 1, 365)
    if error:
        return error

    symbol = request.args.get("symbol")
    if symbol:
        symbol, error = _normalized_symbol(symbol)
        if error:
            return error

    posts = get_sentiment_trends(days, symbol)
    return jsonify({"symbol": symbol, "days": days, "posts": posts})


@api_bp.get("/trends/<symbol>")
def get_ticker_sentiment_trends_specific(symbol: str):
    symbol, error = _normalized_symbol(symbol)
    if error:
        return error
    days, error = _integer_arg("days", 7, 1, 365)
    if error:
        return error

    posts = get_sentiment_trends(days, symbol)
    return jsonify({"symbol": symbol, "days": days, "posts": posts})


@api_bp.get("/health")
def health_check():
    try:
        with get_db_connection() as connection:
            connection.cursor.execute("SELECT 1")
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception:
        return jsonify({"status": "degraded", "database": "disconnected"}), 503


_refresh_in_progress = False
_refresh_lock = threading.Lock()
_scheduler_started = False


def _run_refresh():
    global _refresh_in_progress
    try:
        from src.pipeline.preprocess import ProcessDB

        ProcessDB.ingestAndProcessWeek("posts")
    except Exception:
        logger.exception("Background refresh failed")
    finally:
        with _refresh_lock:
            _refresh_in_progress = False


def _refresh_configuration_errors() -> list[str]:
    reddit_client = os.getenv("REDDIT_CLIENT_ID") or os.getenv("CLIENT_ID")
    reddit_secret = os.getenv("REDDIT_CLIENT_SECRET") or os.getenv("API_KEY")
    missing = []
    if not reddit_client:
        missing.append("REDDIT_CLIENT_ID")
    if not reddit_secret:
        missing.append("REDDIT_CLIENT_SECRET")
    if not os.getenv("DB_CONNECTION_STRING"):
        missing.append("DB_CONNECTION_STRING")
    if not os.getenv("REFRESH_TOKEN"):
        missing.append("REFRESH_TOKEN")
    return missing


def _start_refresh() -> bool:
    global _refresh_in_progress
    with _refresh_lock:
        if _refresh_in_progress:
            return False
        _refresh_in_progress = True

    thread = threading.Thread(target=_run_refresh, daemon=True, name="marketsent-refresh")
    try:
        thread.start()
    except Exception:
        with _refresh_lock:
            _refresh_in_progress = False
        raise
    return True


def start_refresh_scheduler() -> None:
    """Start one in-process scheduler for opportunistic Render refreshes."""

    global _scheduler_started
    enabled = os.getenv("AUTO_REFRESH_ENABLED", "false").lower() in {"1", "true", "yes"}
    if not enabled or _refresh_configuration_errors():
        return

    with _refresh_lock:
        if _scheduler_started:
            return
        _scheduler_started = True

    try:
        interval_seconds = max(3600, int(float(os.getenv("REFRESH_INTERVAL_HOURS", "12")) * 3600))
        start_delay = max(0, int(os.getenv("REFRESH_START_DELAY_SECONDS", "20")))
    except ValueError:
        logger.warning("Invalid refresh scheduler interval; using defaults")
        interval_seconds = 12 * 3600
        start_delay = 20

    def schedule():
        refresh_timer = threading.Event()
        refresh_timer.wait(start_delay)
        while True:
            _start_refresh()
            refresh_timer.wait(interval_seconds)

    threading.Thread(
        target=schedule,
        daemon=True,
        name="marketsent-refresh-scheduler",
    ).start()


@api_bp.post("/refresh")
def refresh():
    """Start a background refresh if the service is configured for scraping."""

    missing = _refresh_configuration_errors()
    if missing:
        return jsonify({"error": "Refresh is not configured", "missing": missing}), 503

    configured_token = os.environ["REFRESH_TOKEN"]
    provided_token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not secrets.compare_digest(provided_token, configured_token):
        return jsonify({"error": "Unauthorized"}), 401

    if not _start_refresh():
        return jsonify({"status": "already_running"}), 200
    return jsonify({"status": "started"}), 202
