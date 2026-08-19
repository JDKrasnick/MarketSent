import { useEffect, useState } from "react";
import { getApiErrorMessage, getTopTickers } from "../services/api";
import type { TickerSentiment } from "../types";


interface TickerResult {
    key: number | null;
    data: TickerSentiment[];
    error: string | null;
}


export function useTickers(days: number = 7) {
    const [result, setResult] = useState<TickerResult>({
        key: null,
        data: [],
        error: null,
    });

    useEffect(() => {
        let active = true;
        getTopTickers(days)
            .then((response) => {
                if (active) setResult({ key: days, data: response.tickers, error: null });
            })
            .catch((error) => {
                if (active) {
                    setResult({
                        key: days,
                        data: [],
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
        loading: !current,
        error: current ? result.error : null,
    };
}
