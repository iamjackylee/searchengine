from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Article, Source

BASE_DIR = Path(__file__).resolve().parent.parent
app = FastAPI(title="ai_news_collector")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _require_token(
    x_api_token: str | None = Header(default=None, alias="X-API-Token"),
    token: str | None = Query(default=None),
) -> None:
    if not settings.api_token:
        return
    if x_api_token != settings.api_token and token != settings.api_token:
        raise HTTPException(status_code=401, detail="Unauthorized")


# ── Helper: build article list from DB ──────────────────────
def _query_articles(
    db: Session,
    since_hours: int = settings.default_since_hours,
    q: str | None = None,
    source: str | None = None,
) -> list[dict]:
    since_dt = datetime.now(tz=timezone.utc) - timedelta(hours=since_hours)

    query: Select = select(Article, Source).join(Source, Source.id == Article.source_id)
    query = query.where(Article.created_at >= since_dt)

    if q:
        like = f"%{q}%"
        query = query.where((Article.title.ilike(like)) | (Article.snippet.ilike(like)))

    if source:
        query = query.where(Source.name.ilike(source))

    query = query.order_by(Article.published_at.desc().nullslast(), Article.created_at.desc())

    rows = db.execute(query).all()
    return [
        {
            "id": article.id,
            "source": src.name,
            "source_type": src.source_type,
            "title": article.title,
            "snippet": article.snippet,
            "url": article.url,
            "canonical_url": article.canonical_url,
            "published_at": article.published_at,
            "created_at": article.created_at,
        }
        for article, src in rows
    ]


def _query_sources(db: Session) -> list[dict]:
    rows = db.scalars(select(Source).order_by(Source.name.asc())).all()
    return [
        {
            "id": row.id,
            "name": row.name,
            "source_type": row.source_type,
            "source_url": row.source_url,
        }
        for row in rows
    ]


# ── Pages ────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(_require_token),
) -> HTMLResponse:
    source_options = _query_sources(db)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "q": "",
            "source": "",
            "since_hours": settings.default_since_hours,
            "sources": source_options,
        },
    )


@app.get("/search", response_class=HTMLResponse)
def search(
    request: Request,
    since_hours: int = settings.default_since_hours,
    q: str = "",
    source: str = "",
    db: Session = Depends(get_db),
    _: None = Depends(_require_token),
) -> HTMLResponse:
    articles = _query_articles(
        db,
        since_hours=since_hours,
        q=q or None,
        source=source or None,
    )
    source_options = _query_sources(db)
    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "q": q,
            "source": source,
            "since_hours": since_hours,
            "articles": articles,
            "sources": source_options,
        },
    )


# ── JSON API (kept for programmatic access) ─────────────────

@app.get("/health")
def health(_: None = Depends(_require_token)) -> dict:
    return {"status": "ok", "service": "ai_news_collector"}


@app.get("/api/sources")
def list_sources(db: Session = Depends(get_db), _: None = Depends(_require_token)) -> list[dict]:
    return _query_sources(db)


@app.get("/api/articles")
def list_articles(
    since_hours: int = settings.default_since_hours,
    q: str | None = None,
    source: str | None = None,
    db: Session = Depends(get_db),
    _: None = Depends(_require_token),
) -> list[dict]:
    return _query_articles(db, since_hours=since_hours, q=q, source=source)
