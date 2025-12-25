import { useState, useEffect } from "react";
import { getTopTickers } from "../services/api";
import { TickerSentiment } from "../types";

export function useTickers(days: number = 7) {
    const [data, setData] = useState<TickerSentiment[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        setLoading(true);
        setError(null);

        getTopTickers(days)
            .then((res) => {
                setData(res.tickers);
            })
            .catch((err) => {
                setError(err.message || "Failed to fetch tickers");
            })
            .finally(() => {
                setLoading(false);
            });
    }, [days]);

    return { data, loading, error };
}