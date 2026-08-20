import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from src.pipeline.snapshot import build_snapshot


def reddit_feed(community: str) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>t3_{community}</id>
        <title>Apple beats expectations in {community}</title>
        <updated>2026-08-18T12:00:00+00:00</updated>
        <link href="https://www.reddit.com/r/{community}/comments/example" />
        <content type="html">&lt;p&gt;$AAPL posts strong profit growth&lt;/p&gt;</content>
      </entry>
    </feed>""".encode()


GOOGLE_NEWS_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><item>
  <guid>news-tesla</guid>
  <title>Tesla shares surge after upgrade</title>
  <link>https://news.google.com/articles/tesla</link>
  <pubDate>Tue, 18 Aug 2026 14:00:00 GMT</pubDate>
  <source>Example Markets</source>
  <description><![CDATA[<p>Analysts see upside for TSLA.</p>]]></description>
</item></channel></rss>"""


class SnapshotTest(unittest.TestCase):
    def test_builds_multi_source_snapshot_with_tickers_and_sentiment(self):
        def fetch(url: str) -> bytes:
            if "news.google.com" in url:
                return GOOGLE_NEWS_FEED
            return reddit_feed("stocks")

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "marketsent.json"
            snapshot = build_snapshot(
                output,
                fetch=fetch,
                now=datetime(2026, 8, 19, 12, tzinfo=timezone.utc),
            )

            self.assertEqual(snapshot["schema_version"], 2)
            self.assertEqual(snapshot["count"], 2)
            self.assertEqual([source["status"] for source in snapshot["sources"]], ["ok", "ok"])
            self.assertEqual({post["source"] for post in snapshot["posts"]}, {"reddit", "google_news"})
            apple_post = next(post for post in snapshot["posts"] if "Apple" in post["text"])
            self.assertEqual(apple_post["tickers"], "AAPL")
            self.assertGreater(apple_post["positive"], apple_post["negative"])
            self.assertEqual(json.loads(output.read_text())["count"], 2)

    def test_marks_partial_reddit_refresh_without_dropping_other_feeds(self):
        def fetch(url: str) -> bytes:
            if "news.google.com" in url:
                return GOOGLE_NEWS_FEED
            if "+" in url:
                raise OSError("combined feed failure")
            if "/r/investing/" in url:
                raise OSError("temporary feed failure")
            community = url.split("/r/", 1)[1].split("/", 1)[0]
            return reddit_feed(community)

        with tempfile.TemporaryDirectory() as directory:
            snapshot = build_snapshot(Path(directory) / "marketsent.json", fetch=fetch)

        reddit = snapshot["sources"][0]
        self.assertEqual(reddit["status"], "partial")
        self.assertEqual(reddit["item_count"], 3)
        self.assertIn("1 of 4", reddit["message"])

    def test_preserves_last_good_source_when_refresh_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "marketsent.json"
            existing = {
                "schema_version": 2,
                "generated_at": "2026-08-18T12:00:00Z",
                "sources": [
                    {
                        "id": "reddit",
                        "name": "Reddit",
                        "status": "ok",
                        "item_count": 1,
                        "updated_at": "2026-08-18T12:00:00Z",
                    }
                ],
                "posts": [
                    {
                        "postid": 1,
                        "text": "Microsoft earnings",
                        "post_text": "MSFT growth",
                        "score": 0,
                        "upvote_ratio": 0,
                        "creation": "2026-08-18",
                        "source": "reddit",
                        "source_name": "Reddit",
                        "publisher": "r/stocks",
                        "source_url": "https://www.reddit.com/example",
                    }
                ],
            }
            output.write_text(json.dumps(existing))
            snapshot = build_snapshot(output, fetch=lambda _url: (_ for _ in ()).throw(OSError("offline")))

        reddit = snapshot["sources"][0]
        self.assertEqual(reddit["status"], "stale")
        self.assertEqual(reddit["updated_at"], "2026-08-18T12:00:00Z")
        self.assertEqual(snapshot["posts"][0]["tickers"], "MSFT")


if __name__ == "__main__":
    unittest.main()
