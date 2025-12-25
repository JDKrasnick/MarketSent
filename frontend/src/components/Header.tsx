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
                <div className="header-meta">
                    <span>{dateStr}</span>
                    <span>{timeStr}</span>
                </div>
            </div>
        </header>
    );
}