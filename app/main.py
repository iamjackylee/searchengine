from __future__ import annotations

import html
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Article, Source

app = FastAPI(title="ai_news_collector")


def _require_token(
    x_api_token: str | None = Header(default=None, alias="X-API-Token"),
    token: str | None = Query(default=None),
) -> None:
    if not settings.api_token:
        return
    if x_api_token != settings.api_token and token != settings.api_token:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/", response_class=HTMLResponse)
def home(
    since_hours: int = settings.default_since_hours,
    q: str = "",
    source: str = "",
    db: Session = Depends(get_db),
    _: None = Depends(_require_token),
) -> str:
    articles = list_articles(
        since_hours=since_hours,
        q=q or None,
        source=source or None,
        db=db,
        _=None,
    )
    source_options = list_sources(db=db, _=None)

    option_html = ["<option value=''>All sources</option>"]
    for src in source_options:
        selected = " selected" if src["name"] == source else ""
        option_html.append(
            f"<option value='{html.escape(src['name'])}'{selected}>{html.escape(src['name'])}</option>"
        )

    rows = []
    for item in articles:
        rows.append(
            """
            <li>
              <a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a><br/>
              <small>{source} • {published}</small>
              <p>{snippet}</p>
            </li>
            """.format(
                url=html.escape(item["url"]),
                title=html.escape(item["title"]),
                source=html.escape(item["source"]),
                published=html.escape(str(item["published_at"] or item["created_at"])),
                snippet=html.escape(item["snippet"][:400]),
            )
        )

    return """
    <html>
      <head>
        <title>AI News Collector</title>
        <style>
          body {{ font-family: Arial, sans-serif; max-width: 920px; margin: 20px auto; padding: 0 10px; }}
          .muted {{ color: #666; }}
          form {{ display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }}
          input, select, button {{ padding: 8px; font-size: 14px; }}
          li {{ margin-bottom: 16px; }}
          p {{ margin: 6px 0; }}
        </style>
      </head>
      <body>
        <h1>AI News Collector</h1>
        <p class="muted">Personal AI news search (independent from Google/Bing)</p>
        <form method="get" action="/">
          <input type="text" name="q" value="{q}" placeholder="Search keywords e.g. open-source model" size="42"/>
          <select name="source">{options}</select>
          <input type="number" min="1" max="720" name="since_hours" value="{since_hours}"/>
          <button type="submit">Search</button>
        </form>
        <p><strong>{count}</strong> result(s)</p>
        <ol>{rows}</ol>
      </body>
    </html>
    """.format(
        q=html.escape(q),
        options="".join(option_html),
        since_hours=since_hours,
        count=len(articles),
        rows="".join(rows) or "<p>No results.</p>",
    )


@app.get("/health")
def health(_: None = Depends(_require_token)) -> dict:
    return {"status": "ok", "service": "ai_news_collector"}


@app.get("/sources")
def list_sources(db: Session = Depends(get_db), _: None = Depends(_require_token)) -> list[dict]:
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


@app.get("/articles")
def list_articles(
    since_hours: int = settings.default_since_hours,
    q: str | None = None,
    source: str | None = None,
    db: Session = Depends(get_db),
    _: None = Depends(_require_token),
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
