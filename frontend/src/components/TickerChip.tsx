import { TickerSentiment } from "../types";

interface TickerChipProps {
    ticker: TickerSentiment;
    isActive?: boolean;
    onClick?: () => void;
}

export function TickerChip({ ticker, isActive = false, onClick }: TickerChipProps) {
    // Calculate net sentiment score
    const netScore = ticker.sentiment.positive - ticker.sentiment.negative;
    const scoreClass = netScore > 0.1 ? "pos" : netScore < -0.1 ? "neg" : "neu";

    return (
        <div
            className={`stock-chip ${isActive ? "active" : ""}`}
            onClick={onClick}
        >
            <span className="chip-ticker">{ticker.symbol}</span>
            <span className={`chip-score ${scoreClass}`}>
                {netScore > 0 ? "+" : ""}
                {(netScore * 100).toFixed(0)}%
            </span>
        </div>
    );
}