"""Reddit ingestion for the MarketSent processing pipeline."""

import os
from datetime import datetime, timezone
from typing import Iterable, Optional

import pandas as pd
import praw
from dotenv import load_dotenv


DEFAULT_SUBREDDITS = ("stocks", "wallstreetbets", "investing", "StockMarket")


class RawDataIngestor:
    """Retrieve raw Reddit submissions for configured finance communities."""

    def __init__(
        self,
        api: Optional["RedditAPIClient"] = None,
        subreddits: Optional[Iterable[str]] = None,
    ):
        load_dotenv()
        configured = os.getenv("REDDIT_SUBREDDITS")
        if subreddits is not None:
            selected = subreddits
        elif configured:
            selected = configured.split(",")
        else:
            selected = DEFAULT_SUBREDDITS

        self.subreddits = tuple(name.strip() for name in selected if name.strip())
        if not self.subreddits:
            raise ValueError("At least one subreddit must be configured")
        self.api = api or RedditAPIClient()

    @property
    def subreddit_expression(self) -> str:
        return "+".join(self.subreddits)

    def get_last_day(self) -> pd.DataFrame:
        return self.api.get_posts_daily(self.subreddit_expression)

    def get_last_week(self) -> pd.DataFrame:
        return self.api.get_posts_weekly(self.subreddit_expression)


class RedditAPIClient:
    """Small read-only PRAW client with explicit credential validation."""

    def __init__(self, reddit=None, limit: Optional[int] = None):
        load_dotenv()
        self.limit = limit or _configured_limit()
        if reddit is not None:
            self.reddit = reddit
            return

        client_id = os.getenv("REDDIT_CLIENT_ID") or os.getenv("CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET") or os.getenv("API_KEY")
        if not client_id or not client_secret:
            raise RuntimeError(
                "Reddit credentials are missing. Set REDDIT_CLIENT_ID and "
                "REDDIT_CLIENT_SECRET."
            )

        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=os.getenv("REDDIT_USER_AGENT", "MarketSent/1.0"),
        )
        self.reddit.read_only = True

    def get_top_posts(self, subreddit: str, period: str = "week") -> pd.DataFrame:
        posts = self.reddit.subreddit(subreddit).top(
            time_filter=period,
            limit=self.limit,
        )
        return pd.DataFrame(posts_to_data(posts))

    def get_posts_daily(self, subreddit: str) -> pd.DataFrame:
        return self.get_top_posts(subreddit, "day")

    def get_posts_weekly(self, subreddit: str) -> pd.DataFrame:
        return self.get_top_posts(subreddit, "week")


def _configured_limit() -> int:
    raw_limit = os.getenv("REDDIT_POST_LIMIT", "100")
    try:
        return max(1, min(int(raw_limit), 1000))
    except ValueError:
        return 100


def posts_to_data(posts) -> dict[str, list]:
    """Convert PRAW submission objects to DataFrame-ready columns."""

    data = {
        "text": [],
        "upvote_ratio": [],
        "score": [],
        "creation": [],
        "tickers": [],
        "positive": [],
        "negative": [],
        "neutral": [],
        "confidence": [],
        "post_text": [],
    }

    for post in posts:
        data["text"].append(post.title)
        data["upvote_ratio"].append(post.upvote_ratio)
        data["score"].append(post.score)
        data["creation"].append(
            datetime.fromtimestamp(post.created_utc, tz=timezone.utc).date()
        )
        data["tickers"].append(None)
        data["positive"].append(None)
        data["negative"].append(None)
        data["neutral"].append(None)
        data["confidence"].append(None)
        data["post_text"].append(post.selftext or "")

    return data
