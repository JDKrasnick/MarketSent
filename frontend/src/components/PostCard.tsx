import type { Post } from "../types";

interface PostCardProps {
    post: Post;
}

export function PostCard({ post }: PostCardProps) {
    const positive = Number.isFinite(post.positive) ? post.positive : 0;
    const negative = Number.isFinite(post.negative) ? post.negative : 0;
    const neutral = Number.isFinite(post.neutral) ? post.neutral : 0;
    const netScore = positive - negative;
    const isPositive = netScore >= 0;
    const parsedDate = new Date(post.creation);
    const formattedDate = Number.isNaN(parsedDate.getTime()) ? "Unknown date" : parsedDate.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
    });

    // Parse tickers from PostgreSQL array format
    const tickers = post.tickers
        ? post.tickers.replace(/[{}]/g, "").split(",").filter(Boolean)
        : [];

    return (
        <article className="post-card">
            <div className="post-header">
                <div className="post-meta">
                    <span className="post-date">{formattedDate}</span>
                    <span className="separator">/</span>
                    <span className="post-source">{post.publisher || post.source_name}</span>
                </div>
                <div className={`post-sentiment ${isPositive ? "positive" : "negative"}`}>
                    {isPositive ? "+" : ""}
                    {(netScore * 100).toFixed(0)}%
                </div>
            </div>
            <h3 className="post-title">
                <a href={post.source_url} target="_blank" rel="noreferrer">
                    {post.text}
                </a>
            </h3>
            {post.post_text && (
                <p className="post-body">{post.post_text.slice(0, 200)}{post.post_text.length > 200 ? "..." : ""}</p>
            )}
            {tickers.length > 0 && (
                <div className="post-tickers">
                    {tickers.map((ticker) => (
                        <span key={ticker} className="post-ticker-tag">
                            {ticker.trim()}
                        </span>
                    ))}
                </div>
            )}
            <div
                className="post-sentiment-bar"
                aria-label={`${(positive * 100).toFixed(0)}% positive, ${(neutral * 100).toFixed(0)}% neutral, ${(negative * 100).toFixed(0)}% negative`}
                role="img"
            >
                <div
                    className="sentiment-segment positive"
                    style={{ width: `${positive * 100}%` }}
                />
                <div
                    className="sentiment-segment neutral"
                    style={{ width: `${neutral * 100}%` }}
                />
                <div
                    className="sentiment-segment negative"
                    style={{ width: `${negative * 100}%` }}
                />
            </div>
        </article>
    );
}
