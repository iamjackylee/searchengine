#!/usr/bin/env python3
"""Fetch news from RSS + GDELT and write to a flat JSON file.

This script is designed to run inside GitHub Actions without a database.
It reads/merges an existing articles.json, fetches new articles from
configured sources, deduplicates, prunes old entries, and writes back.

All shared logic (AI keyword filter, URL canonicalization, constants)
is imported from the ``app`` package to avoid duplication.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests
import yaml
from dateutil import parser as date_parser

# Ensure the repo root is on sys.path so we can import from ``app``
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import settings           # noqa: E402
from app.constants import GDELT_DOC_API   # noqa: E402
from app.filters import is_ai_related     # noqa: E402
from app.utils import canonicalize_url     # noqa: E402

# ── Paths ────────────────────────────────────────────────────
ARTICLES_FILE = ROOT / "site" / "data" / "articles.json"


# ── Helpers ──────────────────────────────────────────────────

def parse_dt(value: str | None) -> str | None:
    """Parse a date string and return ISO-8601, or None."""
    if not value:
        return None
    try:
        dt = date_parser.parse(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except (ValueError, TypeError):
        return None


def load_sources() -> dict:
    """Load source configuration from the YAML file referenced in settings."""
    path = ROOT / settings.sources_file
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data.setdefault("rss_sources", [])
    data.setdefault("gdelt_sources", [])
    return data


def load_existing() -> list[dict]:
    if ARTICLES_FILE.exists():
        with open(ARTICLES_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_articles(articles: list[dict]) -> None:
    ARTICLES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=1)


def _make_article(
    source_name: str,
    source_type: str,
    title: str,
    snippet: str,
    url: str,
    published_at: str | None,
) -> dict | None:
    """Validate, filter, and build a normalised article dict.  Return None to skip."""
    if not title or not url:
        return None
    if not is_ai_related(title, snippet):
        return None
    return {
        "source": source_name,
        "source_type": source_type,
        "title": title.strip(),
        "snippet": (snippet or "").strip(),
        "url": url.strip(),
        "canonical_url": canonicalize_url(url),
        "published_at": published_at,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
    }


# ── Ingestors ────────────────────────────────────────────────

def fetch_rss(rss_sources: list[dict]) -> list[dict]:
    articles: list[dict] = []
    for src in rss_sources:
        name = src["name"]
        url = src["url"]
        try:
            feed = feedparser.parse(url)
        except Exception as exc:
            print(f"  [WARN] RSS {name}: {exc}", file=sys.stderr)
            continue

        for entry in feed.entries:
            pub = parse_dt(entry.get("published") or entry.get("updated"))
            art = _make_article(
                source_name=name,
                source_type="rss",
                title=entry.get("title", ""),
                snippet=entry.get("summary", ""),
                url=entry.get("link", ""),
                published_at=pub,
            )
            if art:
                articles.append(art)
    return articles


def fetch_gdelt(gdelt_sources: list[dict]) -> list[dict]:
    articles: list[dict] = []
    for src in gdelt_sources:
        name = src["name"]
        query = src["query"]
        timespan = src.get("timespan") or settings.gdelt_timespan

        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "sort": "datedesc",
            "timespan": timespan,
        }
        try:
            resp = requests.get(GDELT_DOC_API, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            print(f"  [WARN] GDELT {name}: {exc}", file=sys.stderr)
            continue

        for item in data.get("articles", []):
            snippet = " ".join(filter(None, [
                item.get("domain", ""),
                item.get("sourceCountry", ""),
            ]))
            pub = parse_dt(item.get("seendate"))
            art = _make_article(
                source_name=name,
                source_type="gdelt",
                title=item.get("title", ""),
                snippet=snippet,
                url=item.get("url", ""),
                published_at=pub,
            )
            if art:
                articles.append(art)
    return articles


# ── Merge & prune ────────────────────────────────────────────

def merge(existing: list[dict], new: list[dict]) -> list[dict]:
    """Deduplicate by canonical_url, keeping existing entries on conflict."""
    seen: dict[str, dict] = {}
    for art in existing:
        key = art.get("canonical_url") or art.get("url", "")
        if key not in seen:
            seen[key] = art
    for art in new:
        key = art.get("canonical_url") or art.get("url", "")
        if key not in seen:
            seen[key] = art
    return list(seen.values())


def prune_old(articles: list[dict], max_age_days: int) -> list[dict]:
    cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=max_age_days)).isoformat()
    return [a for a in articles if (a.get("published_at") or a.get("created_at") or "") >= cutoff]


def sort_articles(articles: list[dict]) -> list[dict]:
    return sorted(articles, key=lambda a: a.get("published_at") or a.get("created_at") or "", reverse=True)


# ── Main ─────────────────────────────────────────────────────

def main() -> None:
    sources = load_sources()
    existing = load_existing()
    print(f"Existing articles: {len(existing)}")

    print("Fetching RSS...")
    rss_new = fetch_rss(sources["rss_sources"])
    print(f"  RSS fetched: {len(rss_new)}")

    print("Fetching GDELT...")
    gdelt_new = fetch_gdelt(sources["gdelt_sources"])
    print(f"  GDELT fetched: {len(gdelt_new)}")

    merged = merge(existing, rss_new + gdelt_new)
    print(f"After merge (dedup): {len(merged)}")

    pruned = prune_old(merged, settings.max_age_days)
    print(f"After prune (>{settings.max_age_days}d): {len(pruned)}")

    final = sort_articles(pruned)
    save_articles(final)
    print(f"Saved {len(final)} articles to {ARTICLES_FILE}")


if __name__ == "__main__":
    main()
