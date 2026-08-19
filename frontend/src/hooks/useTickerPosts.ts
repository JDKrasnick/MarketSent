import { useEffect, useState } from "react";
import { getApiErrorMessage, getTickerSentiment } from "../services/api";
import type { Post } from "../types";


interface PostResult {
    key: string | null;
    data: Post[];
    error: string | null;
}


export function useTickerPosts(symbol: string | null, days: number = 7) {
    const key = symbol ? `${days}:${symbol}` : null;
    const [result, setResult] = useState<PostResult>({
        key: null,
        data: [],
        error: null,
    });

    useEffect(() => {
        if (!symbol || !key) return;

        let active = true;
        getTickerSentiment(symbol, days)
            .then((response) => {
                if (active) setResult({ key, data: response.posts, error: null });
            })
            .catch((error) => {
                if (active) {
                    setResult({
                        key,
                        data: [],
                        error: getApiErrorMessage(error, "Unable to load recent posts."),
                    });
                }
            });

        return () => {
            active = false;
        };
    }, [days, key, symbol]);

    if (!key) {
        return { data: [], loading: false, error: null };
    }
    const current = result.key === key;
    return {
        data: current ? result.data : [],
        loading: !current,
        error: current ? result.error : null,
    };
}
