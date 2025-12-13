/**
 * TypeScript type definitions for the MarketSent dashboard.
 *
 * Made to ensure type safety across project
 */

// =============================================================================
// POST TYPES
// =============================================================================

/**
 * A single Reddit post with sentiment analysis data.
 * Matches the 'posts' table schema in PostgreSQL.
 */
export interface Post {
  postId: number;
  text: string;           // Post title
  post_text: string;      // Post body content
  tickers: string;        // Comma-separated ticker symbols (e.g., "AAPL,TSLA")
  positive: number;       // FinBERT positive score (0-1)
  negative: number;       // FinBERT negative score (0-1)
  neutral: number;        // FinBERT neutral score (0-1)
  confidence: number;     // Model confidence
  score: number;          // Reddit score (upvotes - downvotes)
  upvote_ratio: number;   // Reddit upvote ratio (0-1)
  creation: string;       // ISO date string
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
 * Response from GET /api/tickers
 */
export interface TopTickersResponse {
  tickers: TickerSentiment[];
  days: number;
}

/**
 * Response from GET /api/tickers/:symbol
 */
export interface TickerDetailResponse {
  symbol: string;
  post_count: number;
  sentiment: {
    positive: number;
    negative: number;
    neutral: number;
  };
  posts: Post[];
}

// =============================================================================
// TREND TYPES
// =============================================================================

/**
 * A single data point in sentiment time series.
 */
export interface TrendDataPoint {
  date: string;           // ISO date string (YYYY-MM-DD)
  positive: number;       // Average positive sentiment
  negative: number;       // Average negative sentiment
  neutral: number;        // Average neutral sentiment
  post_count: number;     // Number of posts on this date
}

/**
 * Response from GET /api/trends
 */
export interface TrendsResponse {
  days: number;
  trends: TrendDataPoint[];
}

/**
 * Response from GET /api/trends/:symbol
 */
export interface TickerTrendsResponse {
  symbol: string;
  days: number;
  trends: TrendDataPoint[];
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

