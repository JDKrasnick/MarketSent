/**
 * TypeScript type definitions for the MarketSent dashboard.
 *
 * Made to ensure type safety across project
 */

// =============================================================================
// POST TYPES
// =============================================================================

/**
 * A single source item with normalized sentiment data.
 */
export interface Post {
  postid: number;         // Note: lowercase 'id' to match PostgreSQL
  text: string;           // Post title
  post_text: string;      // Post body content
  tickers: string;        // Array format from PostgreSQL (e.g., "{AAPL,TSLA}")
  positive: number;       // FinBERT positive score (0-1)
  negative: number;       // FinBERT negative score (0-1)
  neutral: number;        // FinBERT neutral score (0-1)
  confidence: number;     // Model confidence
  score: number;          // Reddit score (upvotes - downvotes)
  upvote_ratio: number;   // Reddit upvote ratio (0-1)
  creation: string;       // ISO date string
  source: "reddit" | "google_news";
  source_name: string;
  publisher: string;
  source_url: string;
}

export interface SourceStatus {
  id: "reddit" | "google_news";
  name: string;
  status: "ok" | "partial" | "stale";
  item_count: number;
  updated_at: string | null;
  message?: string;
}

/**
 * Recent posts derived from the production snapshot.
 */
export interface PostsResponse {
  posts: Post[];
  time: "day" | "week";
  count: number;
}

// =============================================================================
// TICKER TYPES
// =============================================================================

/**
 * Aggregated sentiment data for a single ticker.
 */
export interface TickerSentiment {
  symbol: string;
  mentions: number;
  sentiment: {
    positive: number;
    negative: number;
    neutral: number;
  };
}

/**
 * Aggregated ticker data derived from the production snapshot.
 */
export interface TopTickersResponse {
  tickers: TickerSentiment[];
  days: number;
  generated_at: string;
  sources: SourceStatus[];
}

/**
 * Source items for one ticker.
 */
export interface TickerDetailResponse {
  posts: Post[];
}

/**
 * Tickers ranked by mention volume and positive momentum.
 */
export interface HotTickersResponse {
  tickers: TickerSentiment[];
  days: number;
}

// =============================================================================
// TREND TYPES
// =============================================================================

/**
 * A single data point in sentiment time series.
 */
export interface TrendDataPoint {
  date: string;           // ISO date string (YYYY-MM-DD)
  avg_positive: number;   // Average positive sentiment
  avg_negative: number;   // Average negative sentiment
  avg_neutral: number;    // Average neutral sentiment
  post_count: number;     // Number of posts on this date
}

/**
 * Daily sentiment averages for the selected market window.
 */
export interface TrendsResponse {
  posts: TrendDataPoint[];
}

// =============================================================================
// API RESPONSE TYPES
// =============================================================================

/**
 * Generic paginated response wrapper.
 */
export interface PaginatedResponse<T> {
  data: T[];
  limit: number;
  offset: number;
  total?: number;
}

/**
 * API error response structure.
 */
export interface ApiError {
  error: string;
  message: string;
}

// =============================================================================
// COMPONENT PROP TYPES
// =============================================================================

/**
 * Common props for chart components.
 */
export interface ChartProps {
  data: TrendDataPoint[];
  loading?: boolean;
  error?: string;
  height?: number;
}

/**
 * Props for ticker selection components.
 */
export interface TickerSelectProps {
  selectedTicker: string | null;
  onSelect: (ticker: string) => void;
  tickers: TickerSentiment[];
}
