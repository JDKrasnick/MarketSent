import { useState, useEffect } from "react";
import { getTickerSentiment } from "../services/api";
import { Post } from "../types";

export function useTickerPosts(symbol: string | null, days: number = 7) {
    const [data, setData] = useState<Post[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!symbol) {
            setData([]);
            return;
        }

        setLoading(true);
        setError(null);

        getTickerSentiment(symbol, days)
            .then((res) => {
                setData(res.posts);
            })
            .catch((err) => {
                setError(err.message || "Failed to fetch posts");
            })
            .finally(() => {
                setLoading(false);
            });
    }, [symbol, days]);

    return { data, loading, error };
}