import { lazy, Suspense, useState } from "react";
import { useTickerPosts, useTickers, useTrends } from "../hooks";
import { Header, Loader, PostCard, ScoreCard, TickerChip } from "../components";
import type { Post, TickerSentiment } from "../types";


const SentimentChart = lazy(() =>
    import("../components/SentimentChart").then((module) => ({
        default: module.SentimentChart,
    }))
);


export function Dashboard() {
    const [selectedTicker, setSelectedTicker] = useState<TickerSentiment | null>(null);
    const days = 30;

    const {
        data: tickers,
        loading: tickersLoading,
        error: tickersError,
    } = useTickers(days);
    const {
        data: trends,
        loading: trendsLoading,
        error: trendsError,
    } = useTrends(days, selectedTicker?.symbol);
    const {
        data: posts,
        loading: postsLoading,
        error: postsError,
    } = useTickerPosts(selectedTicker?.symbol || null, days);

    const allMentions = tickers.reduce((sum, ticker) => sum + ticker.mentions, 0);
    const currentSentiment = selectedTicker?.sentiment || (() => {
        if (allMentions <= 0) {
            return { positive: 0, negative: 0, neutral: 0 };
        }
        return {
            positive: tickers.reduce(
                (sum, ticker) => sum + ticker.sentiment.positive * ticker.mentions,
                0
            ) / allMentions,
            negative: tickers.reduce(
                (sum, ticker) => sum + ticker.sentiment.negative * ticker.mentions,
                0
            ) / allMentions,
            neutral: tickers.reduce(
                (sum, ticker) => sum + ticker.sentiment.neutral * ticker.mentions,
                0
            ) / allMentions,
        };
    })();

    const totalMentions = selectedTicker?.mentions ?? allMentions;
    const selectTicker = (ticker: TickerSentiment | null) => {
        setSelectedTicker(ticker);
        const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
    };

    return (
        <>
            <Header />
            <div className="layout">
                <aside className="sidebar" aria-label="Ticker navigation">
                    <div className="nav-section">
                        <div className="section-label">
                            <span className="label-indicator" aria-hidden="true" />
                            Top Tickers
                        </div>
                        {tickersLoading ? (
                            <Loader />
                        ) : tickersError ? (
                            <p className="error-message" role="alert">{tickersError}</p>
                        ) : (
                            <div className="stock-grid">
                                <button
                                    type="button"
                                    className={`stock-chip ${!selectedTicker ? "active" : ""}`}
                                    onClick={() => selectTicker(null)}
                                    aria-pressed={!selectedTicker}
                                >
                                    <span className="chip-ticker">ALL</span>
                                    <span className="chip-score neu">Overview</span>
                                </button>
                                {tickers.map((ticker) => (
                                    <TickerChip
                                        key={ticker.symbol}
                                        ticker={ticker}
                                        isActive={selectedTicker?.symbol === ticker.symbol}
                                        onClick={() => selectTicker(ticker)}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                </aside>

                <main className="content">
                    <div className="content-header">
                        <div className="header-row">
                            <h1 className="ticker-display">
                                {selectedTicker?.symbol || "Market Overview"}
                            </h1>
                            <div className="status-indicator">
                                <span className="indicator-dot" aria-hidden="true" />
                                Reddit signal
                            </div>
                        </div>
                        <div className="meta-row" aria-live="polite">
                            <span>Last {days} days</span>
                            <span className="separator" aria-hidden="true">·</span>
                            <span>{totalMentions.toLocaleString()} mentions</span>
                        </div>
                    </div>

                    <ScoreCard
                        positive={currentSentiment.positive}
                        negative={currentSentiment.negative}
                        neutral={currentSentiment.neutral}
                    />

                    <section className="sources-section" aria-labelledby="trends-title">
                        <h2 className="section-title" id="trends-title">
                            <span className="title-accent" aria-hidden="true" />
                            Sentiment Over Time
                        </h2>
                        {trendsLoading ? (
                            <Loader />
                        ) : trendsError ? (
                            <p className="error-message" role="alert">{trendsError}</p>
                        ) : trends.length > 0 ? (
                            <Suspense fallback={<Loader />}>
                                <SentimentChart data={trends} height={350} />
                            </Suspense>
                        ) : (
                            <p className="empty-message">No trend data is available for this window.</p>
                        )}
                    </section>

                    {!selectedTicker && (
                        <section className="sources-section" aria-labelledby="tickers-title">
                            <h2 className="section-title" id="tickers-title">
                                <span className="title-accent" aria-hidden="true" />
                                Top Mentioned Tickers
                            </h2>
                            {tickers.length > 0 ? (
                                <div className="sources-list">
                                    {tickers.slice(0, 5).map((ticker) => {
                                        const score = ticker.sentiment.positive - ticker.sentiment.negative;
                                        const isPositive = score >= 0;
                                        return (
                                            <button
                                                type="button"
                                                key={ticker.symbol}
                                                className="source-row"
                                                onClick={() => selectTicker(ticker)}
                                                aria-label={`Show ${ticker.symbol}, ${ticker.mentions} mentions`}
                                            >
                                                <span className="source-info">
                                                    <span className="source-name">{ticker.symbol}</span>
                                                    <span className="source-count">
                                                        {ticker.mentions} mentions
                                                    </span>
                                                </span>
                                                <span className="source-visualization" aria-hidden="true">
                                                    <span className="viz-track">
                                                        <span
                                                            className={`viz-fill ${isPositive ? "positive" : "negative"}`}
                                                            style={{ width: `${Math.min(Math.abs(score) * 100, 100)}%` }}
                                                        >
                                                            <span className="viz-label">
                                                                {isPositive ? "+" : ""}{(score * 100).toFixed(0)}%
                                                            </span>
                                                        </span>
                                                    </span>
                                                </span>
                                            </button>
                                        );
                                    })}
                                </div>
                            ) : (
                                <p className="empty-message">No ticker mentions are available yet.</p>
                            )}
                        </section>
                    )}

                    {selectedTicker && (
                        <section className="posts-section" aria-labelledby="posts-title">
                            <h2 className="section-title" id="posts-title">
                                <span className="title-accent" aria-hidden="true" />
                                Recent Posts
                            </h2>
                            {postsLoading ? (
                                <Loader />
                            ) : postsError ? (
                                <p className="error-message" role="alert">{postsError}</p>
                            ) : posts.length > 0 ? (
                                <div className="posts-list">
                                    {posts.slice(0, 10).map((post: Post) => (
                                        <PostCard key={post.postid} post={post} />
                                    ))}
                                </div>
                            ) : (
                                <p className="empty-message">
                                    No posts found for {selectedTicker.symbol} in this window.
                                </p>
                            )}
                        </section>
                    )}
                </main>
            </div>
        </>
    );
}
