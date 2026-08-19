"""Flask application factory for the MarketSent API and dashboard."""

import logging
import os
from pathlib import Path
from typing import Optional

from flask import Flask, abort, jsonify, request, send_from_directory
from flask_cors import CORS

from src.api.db import DatabaseQueryError
from src.api.routes import api_bp, start_refresh_scheduler


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"


def create_app(config: Optional[dict] = None) -> Flask:
    """Create the Flask app and register API and frontend routes."""

    app = Flask(__name__, static_folder=None)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key-change-me"),
        JSON_SORT_KEYS=False,
    )
    if config:
        app.config.update(config)

    allowed_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": allowed_origins,
                "methods": ["GET", "POST", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
            }
        },
    )

    app.register_blueprint(api_bp, url_prefix="/api")

    @app.after_request
    def apply_response_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'",
        )

        if request.path.startswith("/assets/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif response.content_type and response.content_type.startswith("text/html"):
            response.headers["Cache-Control"] = "no-cache"
        return response

    @app.errorhandler(DatabaseQueryError)
    def database_unavailable(error):
        app.logger.warning("Database query unavailable: %s", error)
        return jsonify({"error": "Database unavailable", "message": str(error)}), 503

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request", "message": str(error)}), 400

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(Exception)
    def internal_error(error):
        app.logger.exception("Unhandled request error")
        return jsonify({"error": "Internal server error"}), 500

    @app.get("/")
    def frontend_index():
        if not (FRONTEND_DIST / "index.html").is_file():
            return jsonify(
                {
                    "status": "api-only",
                    "message": "Frontend build not found; run npm run build --prefix frontend",
                }
            ), 503
        return send_from_directory(FRONTEND_DIST, "index.html")

    @app.get("/<path:path>")
    def frontend_assets(path: str):
        if path.startswith("api/"):
            abort(404)

        requested_file = FRONTEND_DIST / path
        if requested_file.is_file():
            return send_from_directory(FRONTEND_DIST, path)
        if (FRONTEND_DIST / "index.html").is_file():
            return send_from_directory(FRONTEND_DIST, "index.html")
        abort(404)

    start_refresh_scheduler()
    return app


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    port = int(os.environ.get("PORT", os.environ.get("API_PORT", "5000")))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    create_app().run(host="0.0.0.0", port=port, debug=debug)
