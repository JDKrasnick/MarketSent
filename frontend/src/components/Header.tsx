export function Header() {
    const now = new Date();
    const dateStr = now.toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
    });
    const timeStr = now.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
    });

    return (
        <header className="header">
            <div className="header-content">
                <div className="logo">
                    <span className="logo-box"></span>
                    MarketSent
                </div>
                <div className="header-right">
                    <div className="info-control">
                        <button
                            type="button"
                            className="info-button"
                            aria-label="About MarketSent"
                            aria-describedby="marketsent-description"
                        >
                            <span className="info-icon" aria-hidden="true">?</span>
                        </button>
                        <div className="info-tooltip" id="marketsent-description" role="tooltip">
                            <strong>MarketSent</strong> tracks ticker sentiment across Reddit finance
                            communities and current market coverage from Google News. Source snapshots
                            refresh automatically throughout the day.
                        </div>
                    </div>
                    <div className="header-meta">
                        <span>{dateStr}</span>
                        <span>{timeStr}</span>
                    </div>
                </div>
            </div>
        </header>
    );
}
