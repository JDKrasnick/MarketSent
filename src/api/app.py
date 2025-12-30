"""
Flask application factory for the MarketSent API.

This is the main entry point for the Flask backend server.
It creates and configures the Flask application, registers blueprints,
and sets up CORS for frontend communication.

Running the server:
    Development:
        python -m src.api.app
        # or
        flask --app src.api.app run --debug

    Production:
        gunicorn -w 4 -b 0.0.0.0:5000 'src.api.app:create_app()'

Environment Variables:
    FLASK_ENV: 'development' or 'production'
    FLASK_DEBUG: '1' for debug mode
    API_PORT: Port to run on (default: 5000)
"""

import os
from flask import Flask
from flask_cors import CORS

from src.api.routes import api_bp


def create_app(config: dict = None) -> Flask:
    """
    Application factory function.

    Creates and configures a Flask application instance.
    Using the factory pattern allows for easier testing and
    multiple app configurations.

    Args:
        config: Optional configuration dictionary to override defaults

    Returns:
        Configured Flask application instance

    TODO:
        - Add configuration classes for dev/prod/test
        - Set up logging
        - Add error handlers
        - Configure rate limiting
    """
    app = Flask(__name__)

    # ==========================================================================
    # CONFIGURATION
    # ==========================================================================

    # Default configuration
    app.config.update(
        # Secret key for session management (change in production!)
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-change-me'),

        # JSON settings
        JSON_SORT_KEYS=False,  # Preserve key order in responses

        # TODO: Add database URI configuration
        # SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL'),
        # SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Override with provided config
    if config:
        app.config.update(config)

    # ==========================================================================
    # CORS SETUP
    # ==========================================================================

    # Enable CORS for all routes
    # This allows the React frontend to make requests to the API
    # TODO: Restrict origins in production
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",  # Allow all origins (public API)
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # ==========================================================================
    # REGISTER BLUEPRINTS
    # ==========================================================================

    # Register the API routes blueprint
    app.register_blueprint(api_bp, url_prefix='/api')

    # ==========================================================================
    # ERROR HANDLERS
    # ==========================================================================

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        return {'error': 'Bad request', 'message': str(error.description) if hasattr(error, 'description') else 'Invalid request'}, 400

    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors."""
        return {'error': 'Unauthorized', 'message': 'Authentication required'}, 401

    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors."""
        return {'error': 'Forbidden', 'message': 'You do not have permission to access this resource'}, 403

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return {'error': 'Not found', 'message': str(error)}, 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        return {'error': 'Method not allowed', 'message': 'The HTTP method is not allowed for this endpoint'}, 405

    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handle 422 Unprocessable Entity errors."""
        return {'error': 'Unprocessable entity', 'message': 'The request was well-formed but contains invalid data'}, 422

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle 429 Too Many Requests errors."""
        return {'error': 'Too many requests', 'message': 'Rate limit exceeded. Please try again later'}, 429

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        # TODO: Log the error
        return {'error': 'Internal server error', 'message': 'Something went wrong'}, 500

    @app.errorhandler(502)
    def bad_gateway(error):
        """Handle 502 Bad Gateway errors."""
        return {'error': 'Bad gateway', 'message': 'Invalid response from upstream server'}, 502

    @app.errorhandler(503)
    def service_unavailable(error):
        """Handle 503 Service Unavailable errors."""
        return {'error': 'Service unavailable', 'message': 'The server is temporarily unavailable. Please try again later'}, 503

    @app.errorhandler(504)
    def gateway_timeout(error):
        """Handle 504 Gateway Timeout errors."""
        return {'error': 'Gateway timeout', 'message': 'The server took too long to respond'}, 504

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle uncaught exceptions."""
        # TODO: Log the error with full traceback
        return {'error': 'Internal server error', 'message': 'An unexpected error occurred'}, 500

    # ==========================================================================
    # ADDITIONAL SETUP
    # ==========================================================================

    # TODO: Initialize database connection pool
    # TODO: Set up logging
    # TODO: Register CLI commands
    # TODO: Add request/response logging middleware

    return app


# =============================================================================
# DEVELOPMENT SERVER
# =============================================================================

if __name__ == '__main__':
    """
    Run the development server directly.

    Usage:
        python -m src.api.app

    Note: For production, use a proper WSGI server like gunicorn:
        gunicorn -w 4 -b 0.0.0.0:5000 'src.api.app:create_app()'
    """
    app = create_app()

    port = int(os.environ.get('API_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'

    print(f"""
    TPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPW
    Q           MarketSent API Server                         Q
    `PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPc
    Q  Running on: http://localhost:{port}                       Q
    Q  Debug mode: {debug}                                       Q
    Q                                                          Q
    Q  Endpoints:                                              Q
    Q    GET  /api/health         - Health check              Q
    Q    GET  /api/posts          - Get all posts             Q
    Q    GET  /api/posts/search   - Search posts              Q
    Q    GET  /api/tickers        - Top tickers               Q
    Q    GET  /api/tickers/<sym>  - Ticker sentiment          Q
    Q    GET  /api/trends         - Sentiment trends          Q
    Q    GET  /api/trends/<sym>   - Ticker trends             Q
    ZPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP]
    """)

    app.run(host='0.0.0.0', port=port, debug=debug)