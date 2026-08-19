import type {
    PostsResponse,
    TopTickersResponse,
    HotTickersResponse,
    TickerDetailResponse,
    TrendsResponse,
} from "@/types";


const configuredBaseUrl = import.meta.env.VITE_API_URL?.trim();
const API_BASE_URL = (configuredBaseUrl || "/api").replace(/\/+$/, "");
const REQUEST_TIMEOUT_MS = 20_000;


class ApiRequestError extends Error {
    constructor(message: string, readonly status?: number) {
        super(message);
        this.name = "ApiRequestError";
    }
}


async function request<T>(
    path: string,
    params?: Record<string, string | number | undefined>,
    options?: RequestInit
): Promise<T> {
    const query = new URLSearchParams();
    for (const [key, value] of Object.entries(params || {})) {
        if (value !== undefined) query.set(key, String(value));
    }
    const suffix = query.size > 0 ? `?${query.toString()}` : "";
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
        const response = await fetch(`${API_BASE_URL}${path}${suffix}`, {
            ...options,
            headers: {
                Accept: "application/json",
                ...options?.headers,
            },
            signal: controller.signal,
        });

        let payload: unknown;
        try {
            payload = await response.json();
        } catch {
            throw new ApiRequestError("The data service returned an invalid response.", response.status);
        }

        if (!response.ok) {
            const body = payload as { message?: unknown; error?: unknown };
            const detail = typeof body.message === "string"
                ? body.message
                : typeof body.error === "string"
                    ? body.error
                    : `Request failed with status ${response.status}`;
            throw new ApiRequestError(detail, response.status);
        }
        return payload as T;
    } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
            throw new ApiRequestError("The data service took too long to respond. Please try again.");
        }
        throw error;
    } finally {
        window.clearTimeout(timeout);
    }
}


export function getApiErrorMessage(error: unknown, fallback: string): string {
    return error instanceof ApiRequestError ? error.message : fallback;
}


export const getPosts = (time: string = "week"): Promise<PostsResponse> =>
    request("/posts", { time });

export const getTopTickers = (days: number = 7): Promise<TopTickersResponse> =>
    request("/toptickers", { days });

export const getHotTickers = (
    days: number = 7,
    limit: number = 10
): Promise<HotTickersResponse> => request("/hot_tickers", { days, limit });

export const getTickerSentiment = (
    symbol: string,
    days: number = 7
): Promise<TickerDetailResponse> =>
    request(`/tickers/${encodeURIComponent(symbol)}`, { days });

export const getTrends = (
    days: number = 7,
    symbol?: string
): Promise<TrendsResponse> => request("/trends", { days, symbol });

export const getTickerTrends = (
    symbol: string,
    days: number = 7
): Promise<TrendsResponse> =>
    request(`/trends/${encodeURIComponent(symbol)}`, { days });

export const getHealth = (): Promise<{ status: string; database: string }> =>
    request("/health");

export const triggerRefresh = (
    token: string
): Promise<{ status: string; message?: string }> =>
    request("/refresh", undefined, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
    });
