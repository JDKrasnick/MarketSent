import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.api.app import create_app


class ApiRoutesTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True})
        self.client = self.app.test_client()

    @patch("src.api.routes.get_posts_time", return_value=[{"postid": 1}])
    def test_posts_returns_consistent_payload(self, get_posts_time):
        response = self.client.get("/api/posts?time=day&limit=25")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"posts": [{"postid": 1}], "time": "day", "count": 1},
        )
        get_posts_time.assert_called_once_with("day", 25)

    def test_posts_rejects_invalid_period(self):
        response = self.client.get("/api/posts?time=month")
        self.assertEqual(response.status_code, 400)

    @patch("src.api.routes.search_posts_in_db", return_value=[{"postid": 3}])
    def test_search_posts_is_implemented(self, search_posts):
        response = self.client.get("/api/posts/search?q=tesla&limit=20")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["count"], 1)
        search_posts.assert_called_once_with("tesla", 20)

    def test_search_requires_query(self):
        self.assertEqual(self.client.get("/api/posts/search").status_code, 400)

    @patch(
        "src.api.routes.get_hot_ticker_list",
        return_value=[("NVDA", 12, 0.7, 0.1, 0.2)],
    )
    def test_hot_tickers_calls_database_function(self, get_hot_tickers):
        response = self.client.get("/api/hot_tickers?days=14&limit=3")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["tickers"][0]["symbol"], "NVDA")
        get_hot_tickers.assert_called_once_with(14, 3)

    @patch("src.api.routes.get_top_ticker_list", return_value=[])
    def test_numeric_parameters_are_bounded(self, get_top_tickers):
        self.assertEqual(self.client.get("/api/toptickers?days=0").status_code, 400)
        self.assertEqual(self.client.get("/api/toptickers?limit=101").status_code, 400)
        get_top_tickers.assert_not_called()

    @patch("src.api.routes.get_sentiment_by_ticker", return_value=[])
    def test_ticker_is_normalized(self, get_sentiment):
        response = self.client.get("/api/tickers/aapl?days=7")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["symbol"], "AAPL")
        get_sentiment.assert_called_once_with("AAPL", 7)

    def test_ticker_rejects_invalid_symbol(self):
        response = self.client.get("/api/tickers/not%20a%20ticker")
        self.assertEqual(response.status_code, 400)

    @patch("src.api.routes.get_db_connection")
    def test_health_reports_connected_database(self, get_connection):
        connection = MagicMock()
        connection.__enter__.return_value = connection
        get_connection.return_value = connection

        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "healthy")
        connection.cursor.execute.assert_called_once_with("SELECT 1")

    @patch("src.api.routes.get_db_connection", side_effect=ConnectionError("offline"))
    def test_health_reports_database_failure(self, _get_connection):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["status"], "degraded")

    def test_refresh_explains_missing_configuration(self):
        env = {
            "DB_CONNECTION_STRING": "",
            "REDDIT_CLIENT_ID": "",
            "REDDIT_CLIENT_SECRET": "",
            "CLIENT_ID": "",
            "API_KEY": "",
        }
        with patch.dict(os.environ, env, clear=False):
            response = self.client.post("/api/refresh")

        self.assertEqual(response.status_code, 503)
        self.assertIn("DB_CONNECTION_STRING", response.get_json()["missing"])

    @patch("src.api.routes._start_refresh", return_value=True)
    def test_refresh_requires_configured_bearer_token(self, start_refresh):
        env = {
            "DB_CONNECTION_STRING": "postgresql://configured",
            "REDDIT_CLIENT_ID": "client",
            "REDDIT_CLIENT_SECRET": "secret",
            "REFRESH_TOKEN": "refresh-secret",
        }
        with patch.dict(os.environ, env, clear=False):
            unauthorized = self.client.post("/api/refresh")
            accepted = self.client.post(
                "/api/refresh",
                headers={"Authorization": "Bearer refresh-secret"},
            )

        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(accepted.status_code, 202)
        start_refresh.assert_called_once_with()

    def test_frontend_is_served_from_render_web_service(self):
        with tempfile.TemporaryDirectory() as directory:
            dist = Path(directory)
            (dist / "index.html").write_text("<h1>MarketSent</h1>", encoding="utf-8")
            with patch("src.api.app.FRONTEND_DIST", dist):
                response = self.client.get("/")
                nested = self.client.get("/ticker/AAPL")
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"MarketSent", response.data)
                self.assertEqual(response.headers["X-Frame-Options"], "DENY")
                self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
                self.assertEqual(nested.status_code, 200)
                response.close()
                nested.close()


if __name__ == "__main__":
    unittest.main()
