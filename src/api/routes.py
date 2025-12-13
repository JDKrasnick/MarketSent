"""
API route definitions for the sentiment analysis dashboard.

This module defines all REST API endpoints using Flask blueprints.
Each endpoint corresponds to a database query function in db.py.

Endpoints:
    GET /api/posts              - Get all posts (paginated)
    GET /api/posts/search       - Search posts by text
    GET /api/tickers            - Get top mentioned tickers
    GET /api/tickers/<symbol>   - Get sentiment for a specific ticker
    GET /api/trends             - Get overall sentiment trends
    GET /api/trends/<symbol>    - Get sentiment trends for a ticker

Usage:
    from flask import Flask
    from routes import api_bp

    app = Flask(__name__)
    app.register_blueprint(api_bp, url_prefix='/api')
"""
import string

from flask import Blueprint, jsonify, request

from src.api.db import get_db_connection, get_sentiment_by_ticker, get_all_posts, get_sentiment_trends, get_top_ticker_list
from src.pipeline.ingest import RawDataIngestor

#from . import db

# Blueprint for API routes
api_bp = Blueprint('api', __name__)
ingestor = RawDataIngestor()


# =============================================================================
# POSTS ENDPOINTS
# =============================================================================

@api_bp.route('/posts', methods=['GET'])
def get_posts():
    """
    Get top posts over a period of time.

    Query Parameters:
        time (int): Time period to take posts from (either day or week)

    Returns:
        JSON response with posts array and pagination info

    Example:
        GET /api/posts?limit=50&offset=100
    """

    try:
        time = request.args.get('offset')
    except ValueError:
        return jsonify({'message': 'Invalid parameters', 'results': []}), 400

    if time == "day":
        posts = ingestor.get_last_day()
        return jsonify({'posts': posts, 'message': 'Last posts over 24 hours'}), 200

    elif time == "week":
        posts = ingestor.get_last_week()
        return jsonify({'posts': posts, 'message': 'Last posts over 7 days'}), 200

    return jsonify({'message': "No posts returned"}), 400


@api_bp.route('/posts/search', methods=['GET'])
def search_posts():
    """
    Search posts by text content.

    Query Parameters:
        q (str): Search query (required)
        limit (int): Maximum results (default: 50)

    Returns:
        JSON response with matching posts

    Example:
        GET /api/posts/search?q=tesla+earnings&limit=20

    TODO:
        - Validate that 'q' parameter is provided
        - Call db.search_posts()
        - Return results or 400 error if query missing
    """
    # TODO: Implement
    # query = request.args.get('q')
    # if not query:
    #     return jsonify({'error': 'Missing required parameter: q'}), 400
    # limit = request.args.get('limit', 50, type=int)
    # results = db.search_posts(query, limit=limit)
    # return jsonify({'query': query, 'results': results, 'count': len(results)})

    return jsonify({'message': 'Not implemented', 'results': []})


# =============================================================================
# TICKERS ENDPOINTS
# =============================================================================

@api_bp.route('/toptickers', methods=['GET'])
def get_top_tickers():
    """
    Get the most frequently mentioned tickers.

    Query Parameters:
        days (int): Look-back period in days (default: 7)
        limit (int): Number of tickers to return (default: 10)

    Returns:
        JSON response with top tickers and their sentiment

    Example:
        GET /api/tickers?days=30&limit=20

    Response:
        {
            "tickers": [
                {
                    "symbol": "TSLA",
                    "mentions": 150,
                    "sentiment": {
                        "positive": 0.52,
                        "negative": 0.18,
                        "neutral": 0.30
                    }
                },
                ...
            ]
        }
    """

    days = request.args.get('days', 7, type=int)
    data = get_top_ticker_list(days)

    tickers = [
        {
            "symbol": row[0],
            "mentions": row[1],
            "sentiment": {
                "positive": round(row[2], 2) if row[2] else 0,
                "negative": round(row[3], 2) if row[3] else 0,
                "neutral": round(row[4], 2) if row[4] else 0
            }
        }
        for row in data
    ]

    return jsonify({'tickers': tickers, 'days': days}), 200


@api_bp.route('/hot_tickers', methods=['GET'])
def get_hot_tickers():
    """
    Get tickers which are frequently mentioned and have a high sentiment. (Ranked by mentions * 1/(0.01)^x, where x is positive sentiment)

    Query Parameters:
        days (int): Look-back period in days (default: 7)
        limit (int): Number of tickers to return (default: 10)

    Returns:
        JSON response with hot tickers and their sentiment

    Response:
        {
            "tickers": [
                {
                    "symbol": "TSLA",
                    "mentions": 150,
                    "sentiment": {
                        "positive": 0.52,
                        "negative": 0.18,
                        "neutral": 0.30
                    }
                },
                ...
            ]
        }
    """

    days = request.args.get('days', 7, type=int)
    limit = request.args.get('limit', 10, type=int)
    tickers = get_hot_tickers(days=days, limit=limit)

    return jsonify({'tickers': tickers, 'days': days}), 200


@api_bp.route('/tickers/<symbol>', methods=['GET'])
def get_ticker_sentiment(symbol):
    """
    Gets sentiment data for a specific ticker.

    Path Parameters:
        symbol (str): Stock ticker symbol (e.g., AAPL, TSLA)

    Query Parameters:
        days (int): Look-back period in days (optional, default: all time)

    Returns:
        JSON response with posts mentioning the ticker

    Example:
        GET /api/tickers/AAPL
    """

    days = request.args.get('days', 7, type=int)
    print(days)
    posts = get_sentiment_by_ticker(symbol, days)

    return jsonify({'posts': posts}), 200


# =============================================================================
# TRENDS ENDPOINTS
# =============================================================================

@api_bp.route('/trends', methods=['GET'])
def get_ticker_sentiment_trends():
    """
    Get overall sentiment trends over time.

    Query Parameters:
        symbol (str): Stock ticker symbol (e.g., AAPL, TSLA)
        days (int): Look-back period in days (default: 30)

    Returns:
        JSON response with daily sentiment averages

    Example:
        GET /api/trends?days=60

    Response:
        {
            "days": 30,
            "trends": [
                {
                    "date": "2024-01-15",
                    "positive": 0.45,
                    "negative": 0.25,
                    "neutral": 0.30,
                    "post_count": 42
                },
                ...
            ]
        }
    """
    try:
        symbol = request.args.get('symbol')
    except ValueError:
        return jsonify({'message': 'Invalid ticker symbol'}), 400

    days = request.args.get('days', 7, type=int)
    posts = get_sentiment_trends(days, symbol)

    return jsonify({'posts': posts}), 200

@api_bp.route('/trends/<symbol>', methods=['GET'])
def get_ticker_sentiment_trends_specific(symbol):
    """
    Get overall sentiment trends over time.

    Query Parameters:
        symbol (str): Stock ticker symbol (e.g., AAPL, TSLA)
        days (int): Look-back period in days (default: 30)

    Returns:
        JSON response with daily sentiment averages

    Example:
        GET /api/trends?days=60

    Response:
        {
            "days": 30,
            "trends": [
                {
                    "date": "2024-01-15",
                    "positive": 0.45,
                    "negative": 0.25,
                    "neutral": 0.30,
                    "post_count": 42
                },
                ...
            ]
        }
    """

    days = request.args.get('days', 7, type=int)
    posts = get_sentiment_trends(days, symbol)

    return jsonify({'posts': posts}), 200




# =============================================================================
# HEALTH CHECK
# =============================================================================

@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring.

    Returns: JSON response indicating API status

    Example: GET /api/health
    Response: {"status": "healthy", "database": "connected"}
    """

    # TODO: Add actual database connectivity check
    # try:
    #     with db.get_db_connection() as conn:
    #         conn.cursor.execute("SELECT 1")
    #     db_status = "connected"
    # except Exception:
    #     db_status = "disconnected"


    return jsonify({
        'status': 'healthy',
        'database': 'unknown'  # TODO: Implement actual check
    })