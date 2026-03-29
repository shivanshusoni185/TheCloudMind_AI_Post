from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session, load_only

from ..database import get_db
from ..models import News
from ..schemas import NewsResponse, NewsListResponse
from .. import cache

router = APIRouter(prefix="/news", tags=["news"])

# Columns needed for the list view — deliberately excludes image_data (binary blob).
# Loading the blob for every article on the list endpoint was the primary latency
# cause: 100 articles × ~150 KB average = ~15 MB pulled from the DB on every page load.
_LIST_COLS = [
    News.id,
    News.title,
    News.summary,
    News.tags,
    News.published,
    News.created_at,
    News.updated_at,
    News.slug,
    News.image_filename,       # used to detect whether an image exists
    News._image_url_legacy,    # backward-compat legacy URL field
    News.image_mimetype,
]


@router.get("", response_model=list[NewsListResponse])
async def list_news(
    search: Optional[str] = Query(None, description="Search in title and summary"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    db: Session = Depends(get_db),
):
    cache_key = f"news_list:{search or ''}:{tag or ''}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    from sqlalchemy import or_
    query = (
        db.query(News)
        .options(load_only(*_LIST_COLS))
        .filter(News.published == True)
    )

    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(News.title.ilike(term), News.summary.ilike(term))
        )

    if tag:
        query = query.filter(News.tags.ilike(f"%{tag}%"))

    rows = query.order_by(News.created_at.desc()).all()

    for item in rows:
        if isinstance(item.tags, str):
            item.tags = [item.tags.strip()] if item.tags.strip() else []
        elif item.tags is None:
            item.tags = []

    result = [NewsListResponse.model_validate(item) for item in rows]
    cache.set(cache_key, result)
    return result


@router.get("/image/{news_id}")
async def get_news_image(news_id: int, db: Session = Depends(get_db)):
    """Serve image binary from the database."""
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    if not news.image_data:
        raise HTTPException(status_code=404, detail="Image not found")

    return Response(
        content=news.image_data,
        media_type=news.image_mimetype or "image/jpeg",
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "Content-Disposition": f'inline; filename="{news.image_filename or "image.jpg"}"',
        },
    )


@router.get("/by-slug/{slug}", response_model=NewsResponse)
async def get_news_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get a single article by slug (full detail — image_data not needed here)."""
    news = db.query(News).filter(News.slug == slug, News.published == True).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    if isinstance(news.tags, str):
        news.tags = [news.tags.strip()] if news.tags.strip() else []
    elif news.tags is None:
        news.tags = []

    return news


@router.get("/image/by-slug/{slug}")
async def get_news_image_by_slug(slug: str, db: Session = Depends(get_db)):
    """Serve image binary by article slug."""
    news = db.query(News).filter(News.slug == slug).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    if not news.image_data:
        raise HTTPException(status_code=404, detail="Image not found")

    return Response(
        content=news.image_data,
        media_type=news.image_mimetype or "image/jpeg",
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "Content-Disposition": f'inline; filename="{news.image_filename or "image.jpg"}"',
        },
    )


@router.get("/{news_id}", response_model=NewsResponse)
async def get_news(news_id: int, db: Session = Depends(get_db)):
    """Get a single article by ID (backward-compat)."""
    news = db.query(News).filter(News.id == news_id, News.published == True).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    if isinstance(news.tags, str):
        news.tags = [news.tags.strip()] if news.tags.strip() else []
    elif news.tags is None:
        news.tags = []

    return news
