import { useEffect, useState } from "react";
import { getApiErrorMessage, getTickerTrends, getTrends } from "../services/api";
import type { TrendDataPoint } from "../types";


interface TrendResult {
    key: string | null;
    data: TrendDataPoint[];
    error: string | null;
}


export function useTrends(days: number = 7, symbol?: string) {
    const key = `${days}:${symbol || "ALL"}`;
    const [result, setResult] = useState<TrendResult>({
        key: null,
        data: [],
        error: null,
    });

    useEffect(() => {
        let active = true;
        const fetchTrends = symbol
            ? getTickerTrends(symbol, days)
            : getTrends(days);

        fetchTrends
            .then((response) => {
                if (active) setResult({ key, data: response.posts, error: null });
            })
            .catch((error) => {
                if (active) {
                    setResult({
                        key,
                        data: [],
                        error: getApiErrorMessage(error, "Unable to load sentiment trends."),
                    });
                }
            });

        return () => {
            active = false;
        };
    }, [days, key, symbol]);

    const current = result.key === key;
    return {
        data: current ? result.data : [],
        loading: !current,
        error: current ? result.error : null,
    };
}
