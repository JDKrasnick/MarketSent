import { useEffect, useState } from "react";
import { getApiErrorMessage, getTopTickers } from "../services/api";
import type { SourceStatus, TickerSentiment } from "../types";


interface TickerResult {
    key: number | null;
    data: TickerSentiment[];
    generatedAt: string | null;
    sources: SourceStatus[];
    error: string | null;
}


export function useTickers(days: number = 7) {
    const [result, setResult] = useState<TickerResult>({
        key: null,
        data: [],
        generatedAt: null,
        sources: [],
        error: null,
    });

    useEffect(() => {
        let active = true;
        getTopTickers(days)
            .then((response) => {
                if (active) {
                    setResult({
                        key: days,
                        data: response.tickers,
                        generatedAt: response.generated_at,
                        sources: response.sources,
                        error: null,
                    });
                }
            })
            .catch((error) => {
                if (active) {
                    setResult({
                        key: days,
                        data: [],
                        generatedAt: null,
                        sources: [],
                        error: getApiErrorMessage(error, "Unable to load ticker data."),
                    });
                }
            });

        return () => {
            active = false;
        };
    }, [days]);

    const current = result.key === days;
    return {
        data: current ? result.data : [],
        generatedAt: current ? result.generatedAt : null,
        sources: current ? result.sources : [],
        loading: !current,
        error: current ? result.error : null,
    };
}
