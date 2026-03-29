from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session, load_only
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
    db: Session = Depends(get_db),
):
    cache_key = f"news_list:{search or ''}:{tag or ''}"
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
        # tags is a JSON column — cast to text before ILIKE
        query = query.filter(cast(News.tags, Text).ilike(f"%{tag}%"))

    rows = query.order_by(News.created_at.desc()).all()

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
    news = db.query(News).filter(News.id == news_id).first()
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
    news = db.query(News).filter(News.slug == slug, News.published == True).first()  # noqa: E712
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    if isinstance(news.tags, str):
        news.tags = [news.tags.strip()] if news.tags.strip() else []
    elif news.tags is None:
        news.tags = []

    return news


# ── Image by slug ─────────────────────────────────────────────────
@router.get("/image/by-slug/{slug}")
def get_news_image_by_slug(slug: str, db: Session = Depends(get_db)):
    news = db.query(News).filter(News.slug == slug).first()
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
    news = db.query(News).filter(News.id == news_id, News.published == True).first()  # noqa: E712
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    if isinstance(news.tags, str):
        news.tags = [news.tags.strip()] if news.tags.strip() else []
    elif news.tags is None:
        news.tags = []

    return news
