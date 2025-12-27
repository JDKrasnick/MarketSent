import { Post } from "../types";

interface PostCardProps {
    post: Post;
}

export function PostCard({ post }: PostCardProps) {
    const netScore = post.positive - post.negative;
    const isPositive = netScore >= 0;
    const formattedDate = new Date(post.creation).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
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
                    <span className="post-score">Score: {post.score}</span>
                </div>
                <div className={`post-sentiment ${isPositive ? "positive" : "negative"}`}>
                    {isPositive ? "+" : ""}
                    {(netScore * 100).toFixed(0)}%
                </div>
            </div>
            <h3 className="post-title">{post.text}</h3>
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
            <div className="post-sentiment-bar">
                <div
                    className="sentiment-segment positive"
                    style={{ width: `${post.positive * 100}%` }}
                />
                <div
                    className="sentiment-segment neutral"
                    style={{ width: `${post.neutral * 100}%` }}
                />
                <div
                    className="sentiment-segment negative"
                    style={{ width: `${post.negative * 100}%` }}
                />
            </div>
        </article>
    );
}