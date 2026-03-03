#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

echo "[1/5] Starting Postgres with docker compose"
docker compose up -d

echo "[2/5] Installing Python dependencies"
pip install -r requirements.txt

echo "[3/5] Initializing database"
python -m app.init_db

echo "[4/5] Ingesting latest news once"
python -m app.ingest_once

echo "[5/5] Starting app at http://${HOST:-127.0.0.1}:${PORT:-8000}"
uvicorn app.main:app --host "${HOST:-127.0.0.1}" --port "${PORT:-8000}"
