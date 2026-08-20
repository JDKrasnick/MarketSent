# MarketSent

MarketSent is a stock-market sentiment dashboard built from recent investor
discussion and market coverage. It tracks ticker mentions, positive/negative
sentiment, daily trends, and the source items behind each signal.

**Live app:** https://marketsent.jdkrasnick.com/

The production site runs entirely on Vercel. A scheduled GitHub Actions job
refreshes the bundled dataset every six hours, so the dashboard has no sleeping
web service or external runtime dependency.

## Sources and features

- Top weekly posts from r/stocks, r/investing, r/wallstreetbets, and r/StockMarket
- Current stock-market and earnings coverage from Google News RSS
- Company-name, ticker-symbol, and cashtag extraction
- Positive, negative, and neutral financial-language sentiment
- Daily trend visualization and top-mentioned ticker rankings
- Direct links to every source item
- Per-source freshness and partial-outage status
- Last-good-data continuity when a feed is temporarily unavailable

## Production data flow

```text
Reddit Atom feeds ─┐
                   ├─ GitHub Actions ─ sentiment snapshot ─ Vercel
Google News RSS ───┘
```

The `Refresh market data` workflow runs at minute 17 every six hours and can
also be started manually. It downloads both sources, runs the compact ONNX
financial-language model, writes `frontend/public/data/marketsent.json`, and
commits a changed snapshot to `main`. Vercel deploys that commit as a static
frontend and data file.

## Local development

Requirements: Python 3.11+ and Node.js 22+.

```bash
npm ci
npm ci --prefix frontend
python3 scripts/build_snapshot.py
npm run dev --prefix frontend
```

The default snapshot command uses the deterministic sentiment fallback and has
no credentials or Python package dependencies. To reproduce the production
model pass after installing root Node dependencies:

```bash
ONNXRUNTIME_NODE_INSTALL_CUDA=skip npm ci
npm run warm-model
python3 scripts/build_snapshot.py --model
```

Vite serves the generated snapshot from `/data/marketsent.json` and reloads the
dashboard source normally. No Flask process is needed for the production UI.

## Optional Flask API

The repository retains the Flask/PostgreSQL pipeline for local data experiments
and API compatibility. It is not part of the Vercel deployment. To run it,
install `requirements.txt`, configure Reddit API and database variables in
`.env`, and start `python3 -m src.api.app`.

## Verification

```bash
python3 -m unittest discover -s tests -v
npm audit --audit-level=high
npm audit --audit-level=high --prefix frontend
npm run lint --prefix frontend
npm run build --prefix frontend
python3 -m json.tool frontend/public/data/marketsent.json >/dev/null
```

## License

MIT
