from __future__ import annotations

from datetime import datetime

from dateutil import parser as date_parser
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.filters import is_ai_related
from app.models import Article, Source
from app.utils import canonicalize_url


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return date_parser.parse(value)
    except (ValueError, TypeError):
        return None


def get_or_create_source(db: Session, name: str, source_type: str, source_url: str) -> Source:
    existing = db.scalar(select(Source).where(Source.name == name))
    if existing:
        return existing
    source = Source(name=name, source_type=source_type, source_url=source_url)
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def store_article(
    db: Session,
    source: Source,
    title: str,
    snippet: str,
    url: str,
    published_at: datetime | None,
) -> bool:
    if not title or not url:
        return False
    if not is_ai_related(title, snippet):
        return False

    canonical_url = canonicalize_url(url)
    article = Article(
        source_id=source.id,
        title=title.strip(),
        snippet=(snippet or "").strip(),
        url=url.strip(),
        canonical_url=canonical_url,
        published_at=published_at,
    )
    db.add(article)
    try:
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False
