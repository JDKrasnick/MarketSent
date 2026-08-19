# MarketSent

MarketSent is a stock-market sentiment dashboard that analyzes recent Reddit
finance discussions with a compact financial-language model. It tracks ticker mentions, sentiment mix,
daily trends, and the posts behind each signal.

**Live app:** https://marketsent.onrender.com/

The free Render service can take up to a minute to wake after a period of
inactivity. The frontend and API share the same Render origin, so there is no
separate frontend deployment to wake or configure.

## Features

- Sentiment analysis of posts from configurable finance subreddits
- Company-name, ticker-symbol, and cashtag extraction
- Positive, negative, and neutral sentiment breakdowns
- Daily trend visualization and top-mentioned ticker rankings
- Recent source posts for each ticker
- Protected, deduplicating background refresh endpoint

## Stack

- **Frontend:** React, TypeScript, Vite, Recharts
- **Backend:** Python, Flask, Gunicorn, TinyBERT/ONNX
- **Data:** Reddit API, PostgreSQL with an embedded SQLite continuity store
- **Deployment:** One Render web service defined by `render.yaml`

## Local development

Requirements: Python 3.11+ and Node.js 22+. PostgreSQL is recommended for
durable production history; SQLite is used automatically when it is not
configured or temporarily unavailable.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm ci --prefix frontend
ONNXRUNTIME_NODE_INSTALL_CUDA=skip npm ci
```

Create a root `.env` file with the services used by the backend:

```dotenv
# Optional; omit to use the local SQLite continuity store.
DB_CONNECTION_STRING=postgresql://user:password@host:5432/database
SQLITE_FALLBACK_PATH=/tmp/marketsent.db
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=MarketSent/1.0
REDDIT_SUBREDDITS=stocks,wallstreetbets,investing,StockMarket
SENTIMENT_MODEL=mikeysharma/finance-sentiment-analysis
SENTIMENT_DTYPE=fp32
REFRESH_TOKEN=choose_a_long_random_value
```

Optionally initialize a new PostgreSQL database without dropping existing data:

```bash
psql "$DB_CONNECTION_STRING" -f db/schema.sql
```

Start the API and frontend in separate terminals:

```bash
python -m src.api.app
npm run dev --prefix frontend
```

Vite proxies `/api` to Flask during development. A production build is served
directly by Flask:

```bash
npm run build --prefix frontend
gunicorn --bind 0.0.0.0:5000 'src.api.app:create_app()'
```

## Refreshing Reddit data

The scraper reads the configured subreddits, analyzes posts in batches with a
compact financial TinyBERT ONNX model, and inserts new rows while ignoring
duplicate titles. The canonical Render build pre-downloads the 55 MB model;
legacy Python-only deployments install the locked inference runtime on first
use. Exactly one web worker starts a refresh shortly after each wake or deploy
and repeats every 12 hours while the service remains awake. Existing post titles
are filtered out before model inference. `REFRESH_TOKEN` is required only for
manual refresh requests, not automatic scraping.

```bash
curl -X POST http://localhost:5000/api/refresh \
  -H "Authorization: Bearer $REFRESH_TOKEN"
```

You can also run the weekly pipeline directly:

```bash
python -m src.pipeline.preprocess
```

## API

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/health` | GET | API and database readiness |
| `/api/posts?time=week&limit=100` | GET | Recent analyzed posts |
| `/api/posts/search?q=tesla&limit=20` | GET | Search post titles and bodies |
| `/api/toptickers?days=7&limit=10` | GET | Tickers ranked by mentions |
| `/api/hot_tickers?days=7&limit=10` | GET | Mentions ranked with a positive-sentiment boost |
| `/api/tickers/AAPL?days=7` | GET | Posts mentioning one ticker |
| `/api/trends?days=30&symbol=AAPL` | GET | Daily sentiment trends |
| `/api/refresh/status` | GET | Last automatic refresh state and processed count |
| `/api/refresh` | POST | Start an authenticated background refresh |

Numeric query parameters are validated and bounded. Ticker symbols are
normalized to uppercase before querying.

## Verification

```bash
python -m unittest discover -s tests -v
npm run lint --prefix frontend
npm run build --prefix frontend
```

## License

MIT
