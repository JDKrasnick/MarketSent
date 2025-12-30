# MarketSent

  Real-time sentiment analysis dashboard for stock market discussions. Analyzes Reddit posts from finance communities using AI-powered sentiment analysis to track how investors feel about specific tickers.

  Try it out here!: https://market-sent.vercel.app/
  
  (Note: It's possible my Render instance spun down with inactivity, if so visit here to restart it: https://marketsent.onrender.com, then check again)

  ## Features

  - **Sentiment Tracking** - AI-powered analysis of Reddit posts from r/wallstreetbets, r/stocks, and other finance communities
  - **Ticker Analysis** - View sentiment breakdown (positive/negative/neutral) for individual stock tickers
  - **Trend Visualization** - Interactive charts showing sentiment over time
  - **Top Mentions** - See which tickers are being discussed most frequently
  - **Recent Posts** - Browse analyzed posts with sentiment scores


<img width="1702" height="899" alt="Screenshot 2025-12-30 at 12 07 04 AM" src="https://github.com/user-attachments/assets/57324fff-df4d-4ba3-b4b5-b0cb5ac8fe9d" />

  ## Tech Stack

  **Frontend:** React, TypeScript, Vite, Recharts

  **Backend:** Python, Flask, PostgreSQL, FinBERT, Reddit API

  **Deployment:** Vercel (frontend), Render (backend), Supabase (database)

  ## API Endpoints

  | Endpoint                         | Method | Description                                       |
  |----------------------------------|--------|---------------------------------------------------|
  | /api/health                      | GET    | Health check - returns API and database status    |
  | /api/toptickers?days=7           | GET    | Top mentioned tickers with sentiment scores       |
  | /api/hot_tickers?days=7&limit=10 | GET    | Hot tickers ranked by mentions × sentiment        |
  | /api/tickers/<symbol>?days=7     | GET    | Get all posts mentioning a specific ticker        |
  | /api/trends?days=7&symbol=AAPL   | GET    | Overall sentiment trends (optional ticker filter) |
  | /api/trends/<symbol>?days=7      | GET    | Sentiment trends for a specific ticker            |
  | /api/posts?time=week             | GET    | Get posts by time period (day or week)            |

  Query Parameters:
  - days - Look-back period in days (default: 7)
  - limit - Number of results to return
  - time - Time period: "day" or "week"
  - symbol - Stock ticker symbol (e.g., AAPL, TSLA)

=

  ## License

  MIT

