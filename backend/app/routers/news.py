from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session, load_only, defer
from sqlalchemy import or_, cast, Text

from ..database import get_db
from ..models import News
from ..schemas import NewsResponse, NewsListResponse
from .. import cache

router = APIRouter(prefix="/news", tags=["news"])

# Columns for the list view — image_data (binary blob) is intentionally excluded.
# Loading it for every article was the primary latency source.
_LIST_COLS = [
    News.id,
    News.title,
    News.summary,
    News.tags,
    News.published,
    News.created_at,
    News.updated_at,
    News.slug,
    News.image_filename,
    News._image_url_legacy,
    News.image_mimetype,
]

# Only what an image response needs — skips title/summary/content text.
_IMAGE_COLS = [News.id, News.image_data, News.image_mimetype, News.image_filename]

_IMAGE_HEADERS = {
    "Cache-Control": "public, max-age=31536000, immutable",
}


# ── List ──────────────────────────────────────────────────────────
# Declared as sync `def` so FastAPI routes it through its threadpool
# executor, which is the correct pattern for sync SQLAlchemy I/O.
@router.get("", response_model=list[NewsListResponse])
def list_news(
    search: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, ge=1, le=200),
    offset: int = Query(0, ge=0),
    days: Optional[int] = Query(None, ge=1, le=365),
    db: Session = Depends(get_db),
):
    # limit is optional so existing callers (MCP server) still get the full
    # list; the site pages request small pages — the full list is ~1 MB.
    cache_key = f"news_list:{search or ''}:{tag or ''}:{limit}:{offset}:{days}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    query = (
        db.query(News)
        .options(load_only(*_LIST_COLS))
        .filter(News.published == True)  # noqa: E712
    )

    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(News.title.ilike(term), News.summary.ilike(term))
        )

    if tag:
        # tags is a JSON column — cast to text and match the quoted element,
        # so "AI" matches the tag "AI" but not "Email" or "Tailored".
        query = query.filter(cast(News.tags, Text).ilike(f'%"{tag}"%'))

    if days:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        query = query.filter(News.created_at >= since)

    query = query.order_by(News.created_at.desc(), News.id.desc())
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    rows = query.all()

    for item in rows:
        if isinstance(item.tags, str):
            item.tags = [item.tags.strip()] if item.tags.strip() else []
        elif item.tags is None:
            item.tags = []

    result = [NewsListResponse.model_validate(item) for item in rows]
    cache.set(cache_key, result)
    return result


# ── Image by ID ───────────────────────────────────────────────────
# Sync `def` — threadpool handles the blocking DB read.
# nginx caches the response, so the DB is only hit once per image.
@router.get("/image/{news_id}")
def get_news_image(news_id: int, db: Session = Depends(get_db)):
    news = (
        db.query(News)
        .options(load_only(*_IMAGE_COLS))
        .filter(News.id == news_id)
        .first()
    )
    if not news or not news.image_data:
        raise HTTPException(status_code=404, detail="Image not found")

    return Response(
        content=news.image_data,
        media_type=news.image_mimetype or "image/jpeg",
        headers={
            **_IMAGE_HEADERS,
            "Content-Disposition": f'inline; filename="{news.image_filename or "image.jpg"}"',
        },
    )


# ── Article by slug ───────────────────────────────────────────────
@router.get("/by-slug/{slug}", response_model=NewsResponse)
def get_news_by_slug(slug: str, db: Session = Depends(get_db)):
    cache_key = f"news_slug:{slug}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # defer(): the article page fetches the image separately via image_url,
    # so don't pull the binary blob across the wire here.
    news = (
        db.query(News)
        .options(defer(News.image_data))
        .filter(News.slug == slug, News.published == True)  # noqa: E712
        .first()
    )
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    if isinstance(news.tags, str):
        news.tags = [news.tags.strip()] if news.tags.strip() else []
    elif news.tags is None:
        news.tags = []

    result = NewsResponse.model_validate(news)
    cache.set(cache_key, result)
    return result


# ── Image by slug ─────────────────────────────────────────────────
@router.get("/image/by-slug/{slug}")
def get_news_image_by_slug(slug: str, db: Session = Depends(get_db)):
    news = (
        db.query(News)
        .options(load_only(*_IMAGE_COLS))
        .filter(News.slug == slug)
        .first()
    )
    if not news or not news.image_data:
        raise HTTPException(status_code=404, detail="Image not found")

    return Response(
        content=news.image_data,
        media_type=news.image_mimetype or "image/jpeg",
        headers={
            **_IMAGE_HEADERS,
            "Content-Disposition": f'inline; filename="{news.image_filename or "image.jpg"}"',
        },
    )


# ── Article by ID (compat) ────────────────────────────────────────
@router.get("/{news_id}", response_model=NewsResponse)
def get_news(news_id: int, db: Session = Depends(get_db)):
    # defer(): the article page fetches the image separately via image_url,
    # so don't pull the binary blob across the wire here.
    news = (
        db.query(News)
        .options(defer(News.image_data))
        .filter(News.id == news_id, News.published == True)  # noqa: E712
        .first()
    )
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    if isinstance(news.tags, str):
        news.tags = [news.tags.strip()] if news.tags.strip() else []
    elif news.tags is None:
        news.tags = []

    return news
