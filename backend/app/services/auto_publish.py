import html
import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Iterable, Optional

import feedparser
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import News, generate_slug

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 20
USER_AGENT = (
    "Mozilla/5.0 (compatible; TheCloudMindBot/1.0; "
    "+https://cloudmindai.in)"
)


@dataclass(frozen=True)
class FeedConfig:
    topic: str
    url: str
    tags: list[str]


FEEDS: tuple[FeedConfig, ...] = (
    FeedConfig(
        topic="ai-industry",
        url="https://venturebeat.com/category/ai/feed/",
        tags=["AI", "Industry", "Daily Brief"],
    ),
    FeedConfig(
        topic="ai-tech",
        url="https://techcrunch.com/category/artificial-intelligence/feed/",
        tags=["AI", "Technology", "Daily Brief"],
    ),
    FeedConfig(
        topic="ai-research",
        url="https://www.technologyreview.com/feed/",
        tags=["AI", "Research", "Daily Brief"],
    ),
    FeedConfig(
        topic="ai-news",
        url="https://artificialintelligence-news.com/feed/",
        tags=["AI", "News", "Daily Brief"],
    ),
)


def _clean_text(value: str) -> str:
    text = BeautifulSoup(html.unescape(value or ""), "html.parser").get_text(" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _clean_title(title: str) -> str:
    cleaned = _clean_text(title)
    parts = re.split(r"\s[-|]\s", cleaned)
    return parts[0].strip() if parts else cleaned


def _raw_summary_from_entry(entry: dict) -> str:
    candidates = [
        entry.get("summary", ""),
        entry.get("description", ""),
        " ".join(
            _clean_text(part.get("value", ""))
            for part in entry.get("content", [])
            if part.get("value")
        ),
    ]
    for candidate in candidates:
        cleaned = _clean_text(candidate)
        if cleaned:
            return cleaned[:1000]
    return ""


def _enrich_with_openai(title: str, raw_summary: str) -> tuple[str, str, str]:
    """
    Uses GPT-4o-mini to rewrite content and extract image keywords.
    Returns (summary, full_content, image_keywords).
    Falls back to raw values on any error.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set; skipping enrichment")
        fallback = raw_summary[:500] if raw_summary else title
        return fallback, raw_summary or title, title

    try:
        client = OpenAI(api_key=api_key)
        prompt = (
            f"Title: {title}\n"
            f"Raw summary: {raw_summary}\n\n"
            "Return a JSON object with exactly these three keys:\n"
            "  summary: a clean 2-sentence summary suitable for a news card (max 300 chars)\n"
            "  content: a well-written 3-4 paragraph article expanding on this news story\n"
            "  image_keywords: 2-3 concise visual search terms for finding a relevant stock photo "
            "(e.g. 'artificial intelligence robot', 'machine learning data')\n\n"
            "Write in a professional tech news style. Plain text only, no markdown."
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional tech news writer specializing in artificial intelligence. "
                        "Always respond with valid JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=900,
        )
        data = json.loads(response.choices[0].message.content)
        summary = str(data.get("summary", raw_summary))[:500]
        content = str(data.get("content", raw_summary))
        image_keywords = str(data.get("image_keywords", title))
        logger.info("OpenAI enrichment succeeded for: %s", title)
        return summary, content, image_keywords
    except Exception as exc:
        logger.warning("OpenAI enrichment failed for '%s': %s", title, exc)
        fallback = raw_summary[:500] if raw_summary else title
        return fallback, raw_summary or title, title


def _fetch_unsplash_image(keywords: str) -> Optional[str]:
    """Search Unsplash for a free licensed image matching the keywords."""
    access_key = os.getenv("UNSPLASH_ACCESS_KEY")
    if not access_key:
        logger.warning("UNSPLASH_ACCESS_KEY not set; skipping image fetch")
        return None
    try:
        response = requests.get(
            "https://api.unsplash.com/search/photos",
            params={
                "query": keywords,
                "per_page": 1,
                "orientation": "landscape",
                "content_filter": "high",
            },
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        if results:
            url = results[0]["urls"]["regular"]
            logger.info("Unsplash image found for '%s': %s", keywords, url)
            return url
    except Exception as exc:
        logger.warning("Unsplash fetch failed for '%s': %s", keywords, exc)
    return None


def _story_exists(db: Session, title: str, base_slug: str) -> bool:
    return (
        db.query(News.id)
        .filter(or_(News.title == title, News.slug == base_slug))
        .first()
        is not None
    )


def _create_news_item(db: Session, feed: FeedConfig, entry: dict) -> bool:
    raw_title = entry.get("title", "")
    title = _clean_title(raw_title)
    if not title:
        return False

    base_slug = generate_slug(title)
    if _story_exists(db, title, base_slug):
        logger.info("Skipping existing story: %s", title)
        return False
    slug = generate_slug(title, db, News)

    raw_summary = _raw_summary_from_entry(entry)
    summary, content, image_keywords = _enrich_with_openai(title, raw_summary)
    image_url = _fetch_unsplash_image(image_keywords)

    news = News(
        title=title,
        summary=summary,
        content=content,
        tags=feed.tags,
        published=True,
        slug=slug,
        image_data=None,
        image_filename=None,
        image_mimetype=None,
    )
    # Store Unsplash URL in the legacy URL column (no binary blob)
    news._image_url_legacy = image_url

    db.add(news)
    db.commit()
    db.refresh(news)
    logger.info("Published automated %s story: %s", feed.topic, title)
    return True


def _iter_entries(feed: FeedConfig, limit: int) -> Iterable[dict]:
    parsed = feedparser.parse(feed.url)
    if parsed.bozo:
        logger.warning("Feed parser warning for %s: %s", feed.url, parsed.bozo_exception)
    return parsed.entries[:limit]


def run_auto_publish(max_per_topic: int = 5) -> dict[str, int]:
    stats: dict[str, int] = {feed.topic: 0 for feed in FEEDS}
    db = SessionLocal()
    try:
        for feed in FEEDS:
            for entry in _iter_entries(feed, max_per_topic):
                try:
                    created = _create_news_item(db, feed, entry)
                except Exception as exc:
                    db.rollback()
                    logger.exception(
                        "Auto-publish failed for topic %s, entry '%s': %s",
                        feed.topic,
                        entry.get("title"),
                        exc,
                    )
                    continue
                if created:
                    stats[feed.topic] += 1
    finally:
        db.close()
    return stats
