from __future__ import annotations

import argparse
import time
from datetime import datetime

from app.config import settings
from app.ingest_once import main as ingest_once


def run_scheduler(interval_minutes: int) -> None:
    print(f"Starting scheduler. Interval={interval_minutes} minutes")
    while True:
        print(f"[{datetime.utcnow().isoformat()}] Running ingestion...")
        ingest_once()
        time.sleep(interval_minutes * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run periodic ingestion")
    parser.add_argument("--interval-minutes", type=int, default=settings.ingest_interval_minutes)
    args = parser.parse_args()
    run_scheduler(args.interval_minutes)


if __name__ == "__main__":
    main()
