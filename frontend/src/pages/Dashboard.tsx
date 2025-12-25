import { useState } from "react";
import { useTickers, useTrends } from "../hooks";
import {
    Header,
    Loader,
    ScoreCard,
    SentimentChart,
    TickerChip,
} from "../components";
import { TickerSentiment } from "../types";

export function Dashboard() {
    const [selectedTicker, setSelectedTicker] = useState<TickerSentiment | null>(null);
    const [days] = useState(30);

    const { data: tickers, loading: tickersLoading } = useTickers(days);
    const { data: trends, loading: trendsLoading } = useTrends(
        days,
        selectedTicker?.symbol
    );

    // Calculate overall sentiment from trends or selected ticker
    const currentSentiment = selectedTicker?.sentiment || {
        positive: trends.length > 0
            ? trends.reduce((sum, t) => sum + t.positive, 0) / trends.length
            : 0,
        negative: trends.length > 0
            ? trends.reduce((sum, t) => sum + t.negative, 0) / trends.length
            : 0,
        neutral: trends.length > 0
            ? trends.reduce((sum, t) => sum + t.neutral, 0) / trends.length
            : 0,
    };

    const totalMentions = selectedTicker?.mentions ||
        trends.reduce((sum, t) => sum + t.post_count, 0);

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
                                    onClick={() => setSelectedTicker(null)}
                                >
                                    <span className="chip-ticker">ALL</span>
                                    <span className="chip-score neu">Overview</span>
                                </div>
                                {tickers.map((ticker) => (
                                    <TickerChip
                                        key={ticker.symbol}
                                        ticker={ticker}
                                        isActive={selectedTicker?.symbol === ticker.symbol}
                                        onClick={() => setSelectedTicker(ticker)}
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
                </main>
            </div>
        </>
    );
}