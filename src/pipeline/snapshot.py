"""Build the static, multi-source dataset served by the Vercel frontend."""

from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Iterable, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from src.pipeline.sentiment import SentimentPipeline, _heuristic_scores
from src.pipeline.tickers import extract_tickers


USER_AGENT = "Mozilla/5.0 (compatible; MarketSent/2.0; +https://marketsent.jdkrasnick.com)"
REDDIT_COMMUNITIES = ("stocks", "investing", "wallstreetbets", "StockMarket")
REDDIT_ATOM = "https://www.reddit.com/r/{community}/top/.rss?t=week&limit=100"
REDDIT_COMBINED_ATOM = REDDIT_ATOM.format(community="+".join(REDDIT_COMMUNITIES))
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?" + urlencode(
    {
        "q": '(stocks OR earnings OR "stock market") when:7d',
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
    }
)
ATOM_NAMESPACE = "{http://www.w3.org/2005/Atom}"
HTML_SPACE = re.compile(r"\s+")
REDDIT_COMMUNITY_PATH = re.compile(r"reddit\.com/r/([^/]+)", re.IGNORECASE)
MAX_BODY_LENGTH = 600
Fetch = Callable[[str], bytes]


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _plain_text(value: Optional[str]) -> str:
    parser = _TextExtractor()
    parser.feed(html.unescape(value or ""))
    text = HTML_SPACE.sub(" ", " ".join(parser.parts)).strip()
    return text[:MAX_BODY_LENGTH]


def _date_only(value: Optional[str]) -> str:
    if not value:
        return datetime.now(timezone.utc).date().isoformat()
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).date().isoformat()


def _stable_id(source: str, identifier: str) -> int:
    digest = hashlib.sha256(f"{source}:{identifier}".encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def fetch_url(url: str) -> bytes:
    request = Request(
        url,
        headers={"Accept": "application/atom+xml, application/rss+xml", "User-Agent": USER_AGENT},
    )
    with urlopen(request, timeout=30) as response:
        return response.read()


def parse_reddit_atom(payload: bytes, community: Optional[str] = None) -> list[dict]:
    root = ElementTree.fromstring(payload)
    posts = []
    for entry in root.findall(f"{ATOM_NAMESPACE}entry"):
        title = (entry.findtext(f"{ATOM_NAMESPACE}title") or "").strip()
        link_element = entry.find(f"{ATOM_NAMESPACE}link")
        link = link_element.get("href", "") if link_element is not None else ""
        identifier = entry.findtext(f"{ATOM_NAMESPACE}id") or link or title
        body = _plain_text(entry.findtext(f"{ATOM_NAMESPACE}content"))
        community_match = REDDIT_COMMUNITY_PATH.search(link)
        publisher = community_match.group(1) if community_match else community
        if not title or not link:
            continue
        posts.append(
            {
                "postid": _stable_id("reddit", identifier),
                "text": title,
                "post_text": body,
                "score": 0,
                "upvote_ratio": 0,
                "creation": _date_only(entry.findtext(f"{ATOM_NAMESPACE}updated")),
                "source": "reddit",
                "source_name": "Reddit",
                "publisher": f"r/{publisher}" if publisher else "Reddit",
                "source_url": link,
            }
        )
    return posts


def parse_google_news_rss(payload: bytes) -> list[dict]:
    root = ElementTree.fromstring(payload)
    posts = []
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        identifier = item.findtext("guid") or link or title
        publisher = (item.findtext("source") or "Google News").strip()
        body = _plain_text(item.findtext("description"))
        if not title or not link:
            continue
        posts.append(
            {
                "postid": _stable_id("google_news", identifier),
                "text": title,
                "post_text": body,
                "score": 0,
                "upvote_ratio": 0,
                "creation": _date_only(item.findtext("pubDate")),
                "source": "google_news",
                "source_name": "Google News",
                "publisher": publisher,
                "source_url": link,
            }
        )
    return posts


def _collect_reddit(fetch: Fetch) -> tuple[list[dict], Optional[str]]:
    try:
        combined = parse_reddit_atom(fetch(REDDIT_COMBINED_ATOM))
        if combined:
            return combined, None
    except Exception:
        pass

    posts: list[dict] = []
    failed: list[str] = []
    for community in REDDIT_COMMUNITIES:
        try:
            posts.extend(parse_reddit_atom(fetch(REDDIT_ATOM.format(community=community)), community))
        except Exception:  # A single community should not stop the full refresh.
            failed.append(community)
    if not posts:
        raise RuntimeError("all Reddit feeds were unavailable")
    detail = f"{len(failed)} of {len(REDDIT_COMMUNITIES)} feeds unavailable" if failed else None
    return posts, detail


def _collect_google_news(fetch: Fetch) -> tuple[list[dict], Optional[str]]:
    posts = parse_google_news_rss(fetch(GOOGLE_NEWS_RSS))
    if not posts:
        raise RuntimeError("Google News returned no items")
    return posts, None


def _previous_source_posts(previous: dict, source_id: str) -> list[dict]:
    return [post for post in previous.get("posts", []) if post.get("source") == source_id]


def _previous_updated_at(previous: dict, source_id: str) -> Optional[str]:
    for source in previous.get("sources", []):
        if source.get("id") == source_id:
            return source.get("updated_at")
    return None


def _deduplicate(posts: Iterable[dict]) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    unique = []
    for post in posts:
        key = (post["source"], post["text"].casefold())
        if key not in seen:
            seen.add(key)
            unique.append(post)
    return unique


def _analyze(posts: list[dict], use_model: bool) -> None:
    texts = [f"{post['text']} {post['post_text']}".strip() for post in posts]
    if not texts:
        return
    scores = SentimentPipeline().analyze_batch(texts) if use_model else _heuristic_scores(texts)
    for post, (positive, negative, neutral) in zip(posts, scores):
        post["tickers"] = extract_tickers(f"{post['text']} {post['post_text']}") or ""
        post["positive"] = round(float(positive), 6)
        post["negative"] = round(float(negative), 6)
        post["neutral"] = round(float(neutral), 6)
        post["confidence"] = round(max(float(positive), float(negative), float(neutral)), 6)


def build_snapshot(
    output: Path,
    *,
    fetch: Fetch = fetch_url,
    use_model: bool = False,
    now: Optional[datetime] = None,
) -> dict:
    """Fetch every source and atomically write a frontend-ready JSON snapshot."""

    generated_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if output.exists():
        try:
            previous = json.loads(output.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            previous = {}
    else:
        previous = {}

    collectors = (
        ("reddit", "Reddit", _collect_reddit),
        ("google_news", "Google News", _collect_google_news),
    )
    all_posts: list[dict] = []
    sources = []
    for source_id, name, collector in collectors:
        try:
            posts, warning = collector(fetch)
            status = "partial" if warning else "ok"
            updated_at = generated_at.isoformat().replace("+00:00", "Z")
            error = warning
        except Exception as exc:
            posts = _previous_source_posts(previous, source_id)
            status = "stale"
            updated_at = _previous_updated_at(previous, source_id)
            error = str(exc)
        all_posts.extend(posts)
        source = {
            "id": source_id,
            "name": name,
            "status": status,
            "item_count": len(posts),
            "updated_at": updated_at,
        }
        if error:
            source["message"] = error
        sources.append(source)

    posts = _deduplicate(all_posts)
    _analyze(posts, use_model=use_model)
    posts.sort(key=lambda post: (post["creation"], post["postid"]), reverse=True)
    snapshot = {
        "schema_version": 2,
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
        "sources": sources,
        "count": len(posts),
        "posts": posts,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(f"{output.suffix}.tmp")
    temporary.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(output)
    return snapshot
