import axios from "axios";
import {
    PostsResponse,
    TopTickersResponse,
    HotTickersResponse,
    TickerDetailResponse,
    TrendsResponse,
} from "@/types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        "Content-Type": "application/json",
    },
});

// POSTS ENDPOINTS

/**
 * GET /api/posts?time=day|week
 */
export const getPosts = async (time: string = "week"): Promise<PostsResponse> => {
    const response = await api.get("/posts", {
        params: { time },
    });
    return response.data;
};

// TICKERS ENDPOINTS

/**
 * GET /api/toptickers?days=7
 */
export const getTopTickers = async (days: number = 7): Promise<TopTickersResponse> => {
    const response = await api.get("/toptickers", {
        params: { days },
    });
    return response.data;
};

/**
 * GET /api/hot_tickers?days=7&limit=10
 */
export const getHotTickers = async (days: number = 7, limit: number = 10): Promise<HotTickersResponse> => {
    const response = await api.get("/hot_tickers", {
        params: { days, limit },
    });
    return response.data;
};

/**
 * GET /api/tickers/:symbol?days=7
 */
export const getTickerSentiment = async (symbol: string, days: number = 7): Promise<TickerDetailResponse> => {
    const response = await api.get(`/tickers/${symbol}`, {
        params: { days },
    });
    return response.data;
};

// TRENDS ENDPOINTS

/**
 * GET /api/trends?days=7&symbol=X
 */
export const getTrends = async (days: number = 7, symbol?: string): Promise<TrendsResponse> => {
    const response = await api.get("/trends", {
        params: { days, symbol },
    });
    return response.data;
};

/**
 * GET /api/trends/:symbol?days=7
 */
export const getTickerTrends = async (symbol: string, days: number = 7): Promise<TrendsResponse> => {
    const response = await api.get(`/trends/${symbol}`, {
        params: { days },
    });
    return response.data;
};

// HEALTH CHECK

/**
 * GET /api/health
 */
export const getHealth = async (): Promise<{ status: string; database: string }> => {
    const response = await api.get("/health");
    return response.data;
};