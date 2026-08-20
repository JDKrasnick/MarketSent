import type {
    HotTickersResponse,
    Post,
    PostsResponse,
    SourceStatus,
    TickerDetailResponse,
    TickerSentiment,
    TopTickersResponse,
    TrendDataPoint,
    TrendsResponse,
} from "@/types";


const SNAPSHOT_URL = "/data/marketsent.json";
const REQUEST_TIMEOUT_MS = 15_000;


interface MarketSnapshot {
    schema_version: number;
    generated_at: string;
    sources: SourceStatus[];
    posts: Post[];
}


class DataRequestError extends Error {
    constructor(message: string) {
        super(message);
        this.name = "DataRequestError";
    }
}


let snapshotPromise: Promise<MarketSnapshot> | null = null;


async function loadSnapshot(): Promise<MarketSnapshot> {
    if (!snapshotPromise) {
        snapshotPromise = (async () => {
            const controller = new AbortController();
            const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
            try {
                const response = await fetch(SNAPSHOT_URL, {
                    headers: { Accept: "application/json" },
                    cache: "no-cache",
                    signal: controller.signal,
                });
                if (!response.ok) {
                    throw new DataRequestError(`Market data is unavailable (${response.status}).`);
                }
                const payload = await response.json() as Partial<MarketSnapshot>;
                if (
                    payload.schema_version !== 2
                    || typeof payload.generated_at !== "string"
                    || !Array.isArray(payload.sources)
                    || !Array.isArray(payload.posts)
                ) {
                    throw new DataRequestError("Market data is in an unsupported format.");
                }
                return payload as MarketSnapshot;
            } catch (error) {
                snapshotPromise = null;
                if (error instanceof DOMException && error.name === "AbortError") {
                    throw new DataRequestError("Market data took too long to load. Please try again.");
                }
                throw error;
            } finally {
                window.clearTimeout(timeout);
            }
        })();
    }
    return snapshotPromise;
}


function postDate(post: Post): number {
    const value = new Date(`${post.creation}T23:59:59Z`).getTime();
    return Number.isNaN(value) ? 0 : value;
}


function recentPosts(posts: Post[], days: number): Post[] {
    const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;
    return posts.filter((post) => postDate(post) >= cutoff);
}


function symbolsFor(post: Post): string[] {
    return post.tickers
        .replace(/[{}]/g, "")
        .split(",")
        .map((symbol) => symbol.trim().toUpperCase())
        .filter(Boolean);
}


function aggregateTickers(posts: Post[]): TickerSentiment[] {
    const aggregates = new Map<string, {
        mentions: number;
        positive: number;
        negative: number;
        neutral: number;
    }>();
    for (const post of posts) {
        for (const symbol of new Set(symbolsFor(post))) {
            const current = aggregates.get(symbol) || {
                mentions: 0,
                positive: 0,
                negative: 0,
                neutral: 0,
            };
            current.mentions += 1;
            current.positive += post.positive;
            current.negative += post.negative;
            current.neutral += post.neutral;
            aggregates.set(symbol, current);
        }
    }
    return Array.from(aggregates, ([symbol, value]) => ({
        symbol,
        mentions: value.mentions,
        sentiment: {
            positive: value.positive / value.mentions,
            negative: value.negative / value.mentions,
            neutral: value.neutral / value.mentions,
        },
    })).sort((left, right) => right.mentions - left.mentions || left.symbol.localeCompare(right.symbol));
}


function trendData(posts: Post[]): TrendDataPoint[] {
    const daily = new Map<string, {
        count: number;
        positive: number;
        negative: number;
        neutral: number;
    }>();
    for (const post of posts) {
        const current = daily.get(post.creation) || {
            count: 0,
            positive: 0,
            negative: 0,
            neutral: 0,
        };
        current.count += 1;
        current.positive += post.positive;
        current.negative += post.negative;
        current.neutral += post.neutral;
        daily.set(post.creation, current);
    }
    return Array.from(daily, ([date, value]) => ({
        date,
        avg_positive: value.positive / value.count,
        avg_negative: value.negative / value.count,
        avg_neutral: value.neutral / value.count,
        post_count: value.count,
    })).sort((left, right) => left.date.localeCompare(right.date));
}


export function getApiErrorMessage(error: unknown, fallback: string): string {
    return error instanceof DataRequestError ? error.message : fallback;
}


export async function getPosts(time: "day" | "week" = "week"): Promise<PostsResponse> {
    const snapshot = await loadSnapshot();
    const posts = recentPosts(snapshot.posts, time === "day" ? 1 : 7);
    return { posts, time, count: posts.length };
}


export async function getTopTickers(days: number = 7): Promise<TopTickersResponse> {
    const snapshot = await loadSnapshot();
    return {
        tickers: aggregateTickers(recentPosts(snapshot.posts, days)),
        days,
        generated_at: snapshot.generated_at,
        sources: snapshot.sources,
    };
}


export async function getHotTickers(
    days: number = 7,
    limit: number = 10
): Promise<HotTickersResponse> {
    const response = await getTopTickers(days);
    const tickers = [...response.tickers]
        .sort((left, right) => {
            const leftHeat = left.mentions * (1 + left.sentiment.positive - left.sentiment.negative);
            const rightHeat = right.mentions * (1 + right.sentiment.positive - right.sentiment.negative);
            return rightHeat - leftHeat;
        })
        .slice(0, limit);
    return { tickers, days };
}


export async function getTickerSentiment(
    symbol: string,
    days: number = 7
): Promise<TickerDetailResponse> {
    const snapshot = await loadSnapshot();
    const normalized = symbol.trim().toUpperCase();
    const posts = recentPosts(snapshot.posts, days).filter((post) => symbolsFor(post).includes(normalized));
    return { posts };
}


export async function getTrends(
    days: number = 7,
    symbol?: string
): Promise<TrendsResponse> {
    const snapshot = await loadSnapshot();
    const normalized = symbol?.trim().toUpperCase();
    const posts = recentPosts(snapshot.posts, days).filter(
        (post) => !normalized || symbolsFor(post).includes(normalized)
    );
    return { posts: trendData(posts) };
}


export const getTickerTrends = (symbol: string, days: number = 7): Promise<TrendsResponse> =>
    getTrends(days, symbol);


export async function getHealth(): Promise<{
    status: string;
    database: string;
    backend: "static";
}> {
    await loadSnapshot();
    return { status: "healthy", database: "snapshot", backend: "static" };
}
