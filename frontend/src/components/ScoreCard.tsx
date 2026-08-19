interface ScoreCardProps {
    positive: number;
    negative: number;
    neutral: number;
}

export function ScoreCard({ positive, negative, neutral }: ScoreCardProps) {
    const safePositive = Number.isFinite(positive) ? positive : 0;
    const safeNegative = Number.isFinite(negative) ? negative : 0;
    const safeNeutral = Number.isFinite(neutral) ? neutral : 0;
    const netScore = safePositive - safeNegative;
    const isPositive = netScore >= 0;
    const scorePercent = Math.abs(netScore * 100);
    const barWidth = Math.min(scorePercent, 100);

    return (
        <section className="score-section">
            <div className="score-container">
                <div className="score-grid">
                    <div className="score-main">
                        <span className="score-label">Sentiment Score</span>
                        <div className={`score-display ${isPositive ? "positive" : "negative"}`}>
                            <span className="score-sign">{isPositive ? "+" : "−"}</span>
                            <span className="score-number">{scorePercent.toFixed(0)}</span>
                        </div>
                        <div className="score-bar">
                            <div className="bar-track">
                                <div
                                    className={`bar-progress ${isPositive ? "positive" : "negative"}`}
                                    style={{ width: `${barWidth}%` }}
                                ></div>
                            </div>
                        </div>
                    </div>
                    <div className="metrics">
                        <div className="metric-box">
                            <span className="metric-value" style={{ color: "var(--positive)" }}>
                                {(safePositive * 100).toFixed(0)}%
                            </span>
                            <span className="metric-label">Positive</span>
                        </div>
                        <div className="metric-box">
                            <span className="metric-value" style={{ color: "var(--neutral)" }}>
                                {(safeNeutral * 100).toFixed(0)}%
                            </span>
                            <span className="metric-label">Neutral</span>
                        </div>
                        <div className="metric-box">
                            <span className="metric-value" style={{ color: "var(--negative)" }}>
                                {(safeNegative * 100).toFixed(0)}%
                            </span>
                            <span className="metric-label">Negative</span>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
