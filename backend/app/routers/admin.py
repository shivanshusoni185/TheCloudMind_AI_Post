import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import News, generate_slug
from ..schemas import NewsResponse, Token
from ..auth import authenticate_admin, create_access_token, get_current_admin
from .. import cache as news_cache
from ..services.auto_publish import (
    refresh_automated_article_content,
    refresh_automated_article_images,
    run_auto_publish,
)

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_image(file: UploadFile) -> bool:
    if not file.filename:
        return False
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False
    return True


async def read_image_data(file: UploadFile) -> tuple[bytes, str, str]:
    """Read image file and return binary data, filename, and mimetype"""
    image_data = await file.read()

    # Check file size
    if len(image_data) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image size exceeds maximum allowed size of {MAX_IMAGE_SIZE / 1024 / 1024}MB"
        )

    # Determine mimetype
    mimetype = file.content_type or "image/jpeg"

    return image_data, file.filename, mimetype


@router.post("/login", response_model=Token)
async def login(username: str = Form(...), password: str = Form(...)):
    logger.info("Admin login attempt for username: %s", username)

    # Check if username is provided
    if not username:
        logger.warning("Admin login failed: username not provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is required",
        )

    # Check if password is provided
    if not password:
        logger.warning("Admin login failed: password not provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required",
        )

    # Authenticate user
    if not authenticate_admin(username, password):
        logger.warning("Admin login failed: invalid credentials for %s", username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    try:
        access_token = create_access_token(data={"sub": username})
        logger.info("Admin login successful for username: %s", username)
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.exception("Admin login failed while creating access token: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating access token",
        )


@router.post("/news", response_model=NewsResponse)
async def create_news(
    title: str = Form(...),
    summary: str = Form(...),
    content: str = Form(...),
    tags: Optional[str] = Form(None),
    published: bool = Form(False),
    slug: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    import json

    image_data = None
    image_filename = None
    image_mimetype = None

    if image and image.filename:
        if not validate_image(image):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image type. Allowed: jpg, jpeg, png, webp"
            )
        image_data, image_filename, image_mimetype = await read_image_data(image)

    # Parse tags - can be JSON array or comma-separated string
    tags_list = None
    if tags:
        try:
            tags_list = json.loads(tags) if tags.startswith('[') else [t.strip() for t in tags.split(',')]
        except:
            tags_list = [t.strip() for t in tags.split(',')]

    # Generate slug from title if not provided
    if not slug:
        slug = generate_slug(title, db, News)
    else:
        # If custom slug provided, ensure it's URL-safe and unique
        slug = generate_slug(slug, db, News)

    news = News(
        title=title,
        summary=summary,
        content=content,
        tags=tags_list,
        published=published,
        slug=slug,
        image_data=image_data,
        image_filename=image_filename,
        image_mimetype=image_mimetype
    )
    db.add(news)
    db.commit()
    db.refresh(news)
    news_cache.invalidate()
    return news


@router.put("/news/{news_id}", response_model=NewsResponse)
async def update_news(
    news_id: int,
    title: Optional[str] = Form(None),
    summary: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    published: Optional[bool] = Form(None),
    slug: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    import json

    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    title_changed = False
    if title is not None and title != news.title:
        news.title = title
        title_changed = True
    if summary is not None:
        news.summary = summary
    if content is not None:
        news.content = content
    if tags is not None:
        # Parse tags - can be JSON array or comma-separated string
        try:
            tags_list = json.loads(tags) if tags.startswith('[') else [t.strip() for t in tags.split(',')]
        except:
            tags_list = [t.strip() for t in tags.split(',')]
        news.tags = tags_list
    if published is not None:
        news.published = published

    # Handle slug update
    if slug is not None:
        # Admin provided custom slug
        # Exclude current news from uniqueness check
        temp_slug = generate_slug(slug, db, News)
        if temp_slug != news.slug:
            # Check if this slug is taken by another article
            existing = db.query(News).filter(News.slug == temp_slug, News.id != news_id).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Slug '{temp_slug}' is already in use"
                )
            news.slug = temp_slug
    elif title_changed and not news.slug:
        # If title changed and no slug exists, generate one
        news.slug = generate_slug(news.title, db, News)

    if image and image.filename:
        if not validate_image(image):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image type. Allowed: jpg, jpeg, png, webp"
            )
        # Update image data in database
        image_data, image_filename, image_mimetype = await read_image_data(image)
        news.image_data = image_data
        news.image_filename = image_filename
        news.image_mimetype = image_mimetype

    db.commit()
    db.refresh(news)
    news_cache.invalidate()
    return news


@router.delete("/news/{news_id}")
async def delete_news(
    news_id: int,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    db.delete(news)
    db.commit()
    news_cache.invalidate()
    return {"message": "News deleted successfully"}


@router.get("/news", response_model=list[NewsResponse])
async def get_all_news(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    news = db.query(News).order_by(News.created_at.desc()).all()

    # Ensure tags is always a list
    for item in news:
        if isinstance(item.tags, str):
            item.tags = [item.tags.strip()] if item.tags.strip() else []
        elif item.tags is None:
            item.tags = []

    return news


@router.post("/automation/run")
async def run_automation(
    current_admin: str = Depends(get_current_admin)
):
    stats = run_auto_publish()
    news_cache.invalidate()
    return {"message": "Automation run completed", "created": stats}


@router.post("/automation/refresh-images")
async def refresh_automation_images(
    current_admin: str = Depends(get_current_admin)
):
    stats = refresh_automated_article_images()
    news_cache.invalidate()
    return {"message": "Automation images refreshed", "updated": stats}


@router.post("/automation/refresh-content")
async def refresh_automation_content(
    current_admin: str = Depends(get_current_admin)
):
    stats = refresh_automated_article_content()
    news_cache.invalidate()
    return {"message": "Automation content refreshed", "updated": stats}
