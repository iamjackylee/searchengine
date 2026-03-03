from __future__ import annotations

import feedparser
from sqlalchemy.orm import Session

from app.ingestors.common import get_or_create_source, parse_datetime, store_article


def ingest_rss(db: Session, rss_sources: list[dict]) -> int:
    inserted = 0
    for source_cfg in rss_sources:
        name = source_cfg["name"]
        url = source_cfg["url"]
        source = get_or_create_source(db, name=name, source_type="rss", source_url=url)

        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.get("title", "")
            snippet = entry.get("summary", "")
            link = entry.get("link", "")
            published_at = parse_datetime(entry.get("published") or entry.get("updated"))
            if store_article(db, source, title, snippet, link, published_at):
                inserted += 1
    return inserted
