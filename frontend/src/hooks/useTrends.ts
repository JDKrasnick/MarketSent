import { useState, useEffect } from "react";
import { getTrends, getTickerTrends } from "../services/api";
import { TrendDataPoint } from "../types";

export function useTrends(days: number = 7, symbol?: string) {
    const [data, setData] = useState<TrendDataPoint[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        setLoading(true);
        setError(null);

        const fetchTrends = symbol
            ? getTickerTrends(symbol, days)
            : getTrends(days);

        fetchTrends
            .then((res) => {
                setData(res.posts);
            })
            .catch((err) => {
                setError(err.message || "Failed to fetch trends");
            })
            .finally(() => {
                setLoading(false);
            });
    }, [days, symbol]);

    return { data, loading, error };
}