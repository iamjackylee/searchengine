from __future__ import annotations

import requests
from sqlalchemy.orm import Session

from app.config import settings
from app.constants import GDELT_DOC_API
from app.ingestors.common import get_or_create_source, parse_datetime, store_article


def ingest_gdelt(db: Session, gdelt_sources: list[dict], default_timespan: str | None = None) -> int:
    inserted = 0
    for source_cfg in gdelt_sources:
        name = source_cfg["name"]
        query = source_cfg["query"]
        timespan = source_cfg.get("timespan") or default_timespan or settings.gdelt_timespan

        source = get_or_create_source(db, name=name, source_type="gdelt", source_url=GDELT_DOC_API)

        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "sort": "datedesc",
            "timespan": timespan,
        }
        response = requests.get(GDELT_DOC_API, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        for item in data.get("articles", []):
            title = item.get("title", "")
            snippet = " ".join(filter(None, [item.get("domain", ""), item.get("sourceCountry", "")]))
            url = item.get("url", "")
            published_at = parse_datetime(item.get("seendate"))
            if store_article(db, source, title, snippet, url, published_at):
                inserted += 1

    return inserted
