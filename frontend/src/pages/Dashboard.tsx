import { useState, useEffect } from "react";
import { useTickers, useTrends, useTickerPosts } from "../hooks";
import { triggerRefresh } from "../services/api";
import {
    Header,
    Loader,
    PostCard,
    ScoreCard,
    SentimentChart,
    TickerChip,
} from "../components";
import { Post, TickerSentiment } from "../types";

export function Dashboard() {
    const [selectedTicker, setSelectedTicker] = useState<TickerSentiment | null>(null);
    const [days] = useState(30);

    const { data: tickers, loading: tickersLoading } = useTickers(days);
    const { data: trends, loading: trendsLoading } = useTrends(
        days,
        selectedTicker?.symbol
    );
    const { data: posts, loading: postsLoading } = useTickerPosts(
        selectedTicker?.symbol || null,
        days
    );

    // Trigger background refresh on page load
    useEffect(() => {
        triggerRefresh().catch(() => {
            // Silently ignore refresh errors - it's a background task
        });
    }, []);

    // Calculate overall sentiment from selected ticker or aggregate from all tickers
    const currentSentiment = selectedTicker?.sentiment || (() => {
        if (tickers.length === 0) {
            return { positive: 0, negative: 0, neutral: 0 };
        }
        const totalMentions = tickers.reduce((sum, t) => sum + t.mentions, 0);
        return {
            positive: tickers.reduce((sum, t) => sum + t.sentiment.positive * t.mentions, 0) / totalMentions,
            negative: tickers.reduce((sum, t) => sum + t.sentiment.negative * t.mentions, 0) / totalMentions,
            neutral: tickers.reduce((sum, t) => sum + t.sentiment.neutral * t.mentions, 0) / totalMentions,
        };
    })();

    const totalMentions = selectedTicker?.mentions ||
        tickers.reduce((sum, t) => sum + t.mentions, 0);

    return (
        <>
            <Header />
            <div className="layout">
                {/* Sidebar */}
                <aside className="sidebar">
                    <div className="nav-section">
                        <div className="section-label">
                            <span className="label-indicator"></span>
                            Top Tickers
                        </div>
                        {tickersLoading ? (
                            <Loader />
                        ) : (
                            <div className="stock-grid">
                                <div
                                    className={`stock-chip ${!selectedTicker ? "active" : ""}`}
                                    onClick={() => {
                                        setSelectedTicker(null);
                                        window.scrollTo({ top: 0, behavior: "smooth" });
                                    }}
                                >
                                    <span className="chip-ticker">ALL</span>
                                    <span className="chip-score neu">Overview</span>
                                </div>
                                {tickers.map((ticker) => (
                                    <TickerChip
                                        key={ticker.symbol}
                                        ticker={ticker}
                                        isActive={selectedTicker?.symbol === ticker.symbol}
                                        onClick={() => {
                                            setSelectedTicker(ticker);
                                            window.scrollTo({ top: 0, behavior: "smooth" });
                                        }}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                </aside>

                {/* Main Content */}
                <main className="content">
                    <div className="content-header">
                        <div className="header-row">
                            <h1 className="ticker-display">
                                {selectedTicker?.symbol || "Market Overview"}
                            </h1>
                            <div className="status-indicator">
                                <span className="indicator-dot"></span>
                                Live
                            </div>
                        </div>
                        <div className="meta-row">
                            <span>Last {days} days</span>
                            <span className="separator">·</span>
                            <span>{totalMentions.toLocaleString()} mentions</span>
                        </div>
                    </div>

                    {/* Score Section */}
                    <ScoreCard
                        positive={currentSentiment.positive}
                        negative={currentSentiment.negative}
                        neutral={currentSentiment.neutral}
                        mentions={totalMentions}
                    />

                    {/* Chart Section */}
                    <section className="sources-section">
                        <div className="section-title">
                            <span className="title-accent"></span>
                            Sentiment Over Time
                        </div>
                        {trendsLoading ? (
                            <Loader />
                        ) : trends.length > 0 ? (
                            <SentimentChart data={trends} height={350} />
                        ) : (
                            <p style={{ color: "var(--dark-grey)" }}>
                                No trend data available
                            </p>
                        )}
                    </section>

                    {/* Top Tickers List */}
                    {!selectedTicker && (
                        <section className="sources-section">
                            <div className="section-title">
                                <span className="title-accent"></span>
                                Top Mentioned Tickers
                            </div>
                            <div className="sources-list">
                                {tickers.slice(0, 5).map((ticker) => {
                                    const score = ticker.sentiment.positive - ticker.sentiment.negative;
                                    const isPos = score >= 0;
                                    return (
                                        <div
                                            key={ticker.symbol}
                                            className="source-row"
                                            onClick={() => setSelectedTicker(ticker)}
                                            style={{ cursor: "pointer" }}
                                        >
                                            <div className="source-info">
                                                <span className="source-name">{ticker.symbol}</span>
                                                <span className="source-count">
                                                    {ticker.mentions} mentions
                                                </span>
                                            </div>
                                            <div className="source-visualization">
                                                <div className="viz-track">
                                                    <div
                                                        className={`viz-fill ${isPos ? "positive" : "negative"}`}
                                                        style={{
                                                            width: `${Math.abs(score) * 100}%`,
                                                        }}
                                                    >
                                                        <span className="viz-label">
                                                            {isPos ? "+" : ""}
                                                            {(score * 100).toFixed(0)}%
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </section>
                    )}

                    {/* Posts Section - Shows when ticker is selected */}
                    {selectedTicker && (
                        <section className="posts-section">
                            <div className="section-title">
                                <span className="title-accent"></span>
                                Recent Posts
                            </div>
                            {postsLoading ? (
                                <Loader />
                            ) : posts.length > 0 ? (
                                <div className="posts-list">
                                    {posts.slice(0, 10).map((post: Post) => (
                                        <PostCard key={post.postid} post={post} />
                                    ))}
                                </div>
                            ) : (
                                <p className="no-posts">
                                    No posts found for {selectedTicker.symbol}
                                </p>
                            )}
                        </section>
                    )}
                </main>
            </div>
        </>
    );
}