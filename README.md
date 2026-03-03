# ai_news_collector

A beginner-friendly **FastAPI + Postgres** app that ingests AI-related news from RSS feeds and the GDELT DOC API, then lets you search in your browser.

## What you get

- Docker Compose for Postgres
- SQLAlchemy models: `sources`, `articles`
- Ingestors:
  - RSS ingestor reading `data/sources.yaml`
  - GDELT DOC API ingestor (`mode=artlist`, `format=json`, `sort=datedesc`, configurable `timespan`)
- AI keyword filter over `title + snippet`
- Dedup by canonical URL unique constraint
- Scheduler CLI for ingestion every 15 minutes
- Optional API token protection (`X-API-Token`)
- Endpoints:
  - `GET /` (simple browser search page)
  - `GET /health`
  - `GET /articles?since_hours=24&q=...&source=...`
  - `GET /sources`

## Super simple run (recommended)

1. Copy env file:
   ```bash
   cp .env.example .env
   ```
2. Start everything:
   ```bash
   ./start.sh
   ```
3. Open browser:
   - `http://127.0.0.1:8000/`

## Manual run

```bash
docker compose up -d
pip install -r requirements.txt
python -m app.init_db
python -m app.ingest_once
uvicorn app.main:app --reload
```

## Scheduler

```bash
python -m app.scheduler --interval-minutes 15
```

## GitHub Actions (free plan safe setup)

This repo includes:
- `CI` workflow on push/PR (quick checks).
- `Hourly Ingest` workflow (`cron`) with concurrency + timeout to reduce minute usage.

### Important notes for free plan

- Hourly is much safer than every 15 minutes for usage limits.
- Keep jobs short and avoid running the web server inside Actions.
- Use an external Postgres (`DATABASE_URL` secret), because runner disks are temporary.

## Database size guidance (practical)

There is no strict DB limit from this code itself, but practical limits come from where Postgres is hosted:
- local Docker volume size on your machine
- or managed DB plan quota (depends on provider)

For personal usage, start with a retention policy idea such as:
- keep only the latest 30–90 days
- archive older rows if needed

## Security tips

- Keep this repo private.
- Do not commit real credentials.
- If you set `API_TOKEN` in `.env`, send `X-API-Token` in requests.
