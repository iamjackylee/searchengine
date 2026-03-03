from __future__ import annotations

from app.database import SessionLocal
from app.ingestors.gdelt_ingestor import ingest_gdelt
from app.ingestors.rss_ingestor import ingest_rss
from app.load_sources import load_sources


def main() -> None:
    sources = load_sources()
    db = SessionLocal()
    try:
        rss_count = ingest_rss(db, sources.get("rss_sources", []))
        gdelt_count = ingest_gdelt(db, sources.get("gdelt_sources", []))
    finally:
        db.close()

    print(f"Ingestion complete. rss={rss_count}, gdelt={gdelt_count}, total={rss_count + gdelt_count}")


if __name__ == "__main__":
    main()
