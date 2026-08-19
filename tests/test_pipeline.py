import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd

from db import connection as database_connection
from src.pipeline.ingest import RawDataIngestor, RedditAPIClient, posts_to_data
from src.pipeline.preprocess import ProcessDB, _insert_ignoring_duplicate_titles
from src.pipeline.sentiment import PROJECT_ROOT, SentimentPipeline, _ensure_node_runtime


class FakeSentimentModel:
    def analyze_batch(self, texts):
        return np.array([[0.7, 0.1, 0.2] for _ in texts])


class PipelineTest(unittest.TestCase):
    def test_ticker_extraction_supports_cashtags_symbols_and_names(self):
        self.assertEqual(
            ProcessDB.getTickers("$AAPL and NVDA challenge Microsoft"),
            "AAPL,NVDA,MSFT",
        )
        self.assertEqual(ProcessDB.getTickers("Berkshire Hathaway owns Apple"), "BRK.B,AAPL")

    def test_ticker_extraction_avoids_common_false_positives(self):
        self.assertIsNone(ProcessDB.getTickers("a new price target after the CEO interview"))
        self.assertEqual(ProcessDB.getTickers("Target raises its guidance"), "TGT")
        self.assertEqual(ProcessDB.getTickers("$F shares moved"), "F")

    def test_process_adds_sentiment_confidence_and_tickers(self):
        raw = pd.DataFrame(
            [
                {
                    "text": "Apple earnings",
                    "post_text": "AAPL beat expectations",
                    "positive": None,
                    "negative": None,
                    "neutral": None,
                    "confidence": None,
                    "tickers": None,
                }
            ]
        )

        result = ProcessDB.processR(raw, FakeSentimentModel())

        self.assertAlmostEqual(result.loc[0, "positive"], 0.7)
        self.assertAlmostEqual(result.loc[0, "confidence"], 0.7)
        self.assertEqual(result.loc[0, "tickers"], "AAPL")

    def test_empty_dataframe_does_not_invoke_model(self):
        model = FakeSentimentModel()
        with patch.object(model, "analyze_batch") as analyze:
            result = ProcessDB.processR(pd.DataFrame(), model)
        self.assertTrue(result.empty)
        analyze.assert_not_called()

    def test_reddit_posts_use_utc_date_and_include_confidence_column(self):
        post = SimpleNamespace(
            title="Market post",
            selftext="Body",
            upvote_ratio=0.9,
            score=42,
            created_utc=0,
        )

        data = posts_to_data([post])

        self.assertEqual(data["creation"], [date(1970, 1, 1)])
        self.assertIn("confidence", data)

    def test_reddit_client_uses_top_period_and_configured_limit(self):
        listing = SimpleNamespace(top=lambda **kwargs: [
            SimpleNamespace(
                title="Post",
                selftext="",
                upvote_ratio=1,
                score=1,
                created_utc=0,
            )
        ])
        reddit = SimpleNamespace(subreddit=lambda name: listing)
        client = RedditAPIClient(reddit=reddit, limit=123)

        frame = client.get_posts_weekly("stocks+investing")

        self.assertEqual(len(frame), 1)

    def test_scraper_requires_credentials(self):
        env = {
            "REDDIT_CLIENT_ID": "",
            "REDDIT_CLIENT_SECRET": "",
            "CLIENT_ID": "",
            "API_KEY": "",
        }
        with patch.dict(os.environ, env, clear=False):
            with self.assertRaisesRegex(RuntimeError, "Reddit credentials are missing"):
                RedditAPIClient()

    def test_ingestor_combines_configured_subreddits(self):
        api = SimpleNamespace(get_posts_weekly=lambda expression: expression)
        ingestor = RawDataIngestor(api=api, subreddits=["stocks", "investing"])
        self.assertEqual(ingestor.get_last_week(), "stocks+investing")

    @patch("src.pipeline.sentiment.subprocess.run")
    def test_sentiment_runner_normalizes_node_response(self, run):
        run.return_value = SimpleNamespace(
            returncode=0,
            stdout='{"scores":[{"positive":0.7,"negative":0.1,"neutral":0.2}]}',
            stderr="",
        )

        scores = SentimentPipeline().analyze("Strong earnings")

        self.assertEqual(scores, [[0.7, 0.1, 0.2]])
        self.assertIn("Strong earnings", run.call_args.kwargs["input"])

    @patch("src.pipeline.sentiment.subprocess.run")
    def test_sentiment_runner_surfaces_inference_failure(self, run):
        run.return_value = SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="Error: model unavailable\n",
        )

        with self.assertRaisesRegex(RuntimeError, "model unavailable"):
            SentimentPipeline().analyze("Text")

    def test_sentiment_runtime_installs_missing_node_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            dependency = Path(directory) / "node_modules" / "transformers"

            def install_runtime(*_args, **_kwargs):
                dependency.mkdir(parents=True)
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with patch("src.pipeline.sentiment.NODE_DEPENDENCY", dependency):
                with patch(
                    "src.pipeline.sentiment.subprocess.run",
                    side_effect=install_runtime,
                ) as run:
                    _ensure_node_runtime()

            command = run.call_args.args[0]
            self.assertEqual(command[:2], ["npm", "ci"])
            self.assertEqual(run.call_args.kwargs["cwd"], PROJECT_ROOT)

    @patch("src.pipeline.preprocess.SentimentPipeline")
    @patch("src.pipeline.preprocess.RawDataIngestor")
    @patch.object(ProcessDB, "_engine")
    def test_ingest_skips_existing_posts_before_loading_model(
        self, get_engine, ingestor_class, sentiment_class
    ):
        raw = pd.DataFrame(
            [{"text": "Already analyzed", "post_text": "Body"}]
        )
        ingestor_class.return_value.get_last_week.return_value = raw
        connection = get_engine.return_value.connect.return_value
        connection.__enter__.return_value.execute.return_value.scalars.return_value = [
            "Already analyzed"
        ]

        result = ProcessDB._ingest("week", "posts")

        self.assertTrue(result.empty)
        sentiment_class.assert_not_called()

    def test_ingest_rejects_unsafe_table_name(self):
        with self.assertRaisesRegex(ValueError, "Invalid database table name"):
            ProcessDB._ingest("week", "posts; DROP TABLE posts")

    def test_sqlite_insert_ignores_duplicate_titles(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {
                "DB_CONNECTION_STRING": "",
                "SQLITE_FALLBACK_PATH": str(Path(directory) / "marketsent.db"),
            }
            frame = pd.DataFrame(
                [
                    {
                        "text": "Unique title",
                        "tickers": "AAPL",
                        "positive": 0.8,
                        "negative": 0.1,
                        "neutral": 0.1,
                        "confidence": 0.8,
                        "post_text": "Body",
                        "score": 1,
                        "upvote_ratio": 1.0,
                        "creation": date.today(),
                    }
                ]
            )
            with patch.dict(os.environ, env, clear=False):
                database_connection.reset_engine()
                try:
                    engine = database_connection.get_engine()
                    for _ in range(2):
                        frame.to_sql(
                            "posts",
                            engine,
                            if_exists="append",
                            index=False,
                            method=_insert_ignoring_duplicate_titles,
                        )
                    with engine.connect() as connection:
                        count = connection.exec_driver_sql(
                            "SELECT COUNT(*) FROM posts"
                        ).scalar_one()
                    self.assertEqual(count, 1)
                finally:
                    database_connection.reset_engine()


if __name__ == "__main__":
    unittest.main()
