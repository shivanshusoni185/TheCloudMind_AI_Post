import html
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.parse import quote, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
from requests import Response
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import News, generate_slug

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 20
MAX_IMAGE_BYTES = 10 * 1024 * 1024
REQUEST_RETRY_DELAYS = (1, 2, 4)
USER_AGENT = (
    "Mozilla/5.0 (compatible; TheCloudMindBot/1.0; "
    "+https://cloudmindai.in)"
)
GOOGLE_NEWS_HOSTS = {"news.google.com", "google.com"}
PLACEHOLDER_IMAGE_HOSTS = {
    "lh3.googleusercontent.com",
    "lh4.googleusercontent.com",
    "lh5.googleusercontent.com",
    "lh6.googleusercontent.com",
    "www.gstatic.com",
}


@dataclass(frozen=True)
class FeedConfig:
    topic: str
    url: str
    tags: list[str]


FEEDS: tuple[FeedConfig, ...] = (
    FeedConfig(
        topic="ai",
        url="https://techcrunch.com/category/artificial-intelligence/feed/",
        tags=["AI", "Automation", "Daily Brief"],
    ),
    FeedConfig(
        topic="ai",
        url="https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        tags=["AI", "Automation", "Daily Brief"],
    ),
    FeedConfig(
        topic="sports",
        url="https://feeds.bbci.co.uk/sport/rss.xml",
        tags=["Sports", "Automation", "Daily Brief"],
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


def _summary_from_entry(entry: dict) -> str:
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
            return cleaned[:500]
    return "Auto-curated story. Open the source link for the full article."


def _content_from_summary(summary: str, source_url: str, topic: str) -> str:
    paragraphs = [
        summary,
        (
            f"This {topic} story was automatically aggregated for the daily "
            "morning update."
        ),
        f"Original source: {source_url}",
    ]
    return "\n\n".join(paragraphs)


def _extract_image_url(entry: dict, article_html: Optional[str]) -> Optional[str]:
    if article_html:
        soup = BeautifulSoup(article_html, "html.parser")
        selectors = [
            ("meta", {"property": "og:image"}),
            ("meta", {"name": "twitter:image"}),
            ("meta", {"property": "og:image:url"}),
        ]
        for tag_name, attrs in selectors:
            tag = soup.find(tag_name, attrs=attrs)
            if tag and tag.get("content"):
                url = tag["content"].strip()
                if not _is_placeholder_image_url(url):
                    return url

    for key in ("media_content", "media_thumbnail"):
        media_items = entry.get(key) or []
        for item in media_items:
            url = item.get("url")
            if url and not _is_placeholder_image_url(url):
                return url

    return None


def _is_placeholder_image_url(image_url: str) -> bool:
    parsed = urlparse(image_url)
    host = parsed.netloc.lower()
    return host in PLACEHOLDER_IMAGE_HOSTS


def _extract_source_url_from_content(content: str) -> Optional[str]:
    match = re.search(r"Original source:\s*(https?://\S+)", content or "")
    return match.group(1).strip() if match else None


def _decode_google_news_url(source_url: str) -> str:
    parsed = urlparse(source_url)
    if parsed.netloc not in GOOGLE_NEWS_HOSTS or "/rss/articles/" not in parsed.path:
        return source_url

    article_id = parsed.path.rstrip("/").split("/")[-1]
    article_page = _request_with_retries(
        "GET",
        f"https://news.google.com/articles/{article_id}",
    )

    signature = re.search(r'data-n-a-sg="([^"]+)"', article_page.text)
    timestamp = re.search(r'data-n-a-ts="([^"]+)"', article_page.text)
    if not signature or not timestamp:
        logger.warning("Could not decode Google News URL, using wrapper: %s", source_url)
        return source_url

    payload = [
        "Fbv4je",
        (
            "[\"garturlreq\",[[\"X\",\"X\",[\"X\",\"X\"],null,null,1,1,"
            "\"US:en\",null,1,null,null,null,null,null,0,1],\"X\",\"X\",1,"
            f"[1,1,1],1,1,null,0,0,null,0],\"{article_id}\",{timestamp.group(1)},"
            f"\"{signature.group(1)}\"]"
        ),
    ]

    response = _request_with_retries(
        "POST",
        "https://news.google.com/_/DotsSplashUi/data/batchexecute",
        data=f"f.req={quote(json.dumps([[payload]]))}",
        headers={
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        },
    )

    decoded_match = re.search(
        r'\["garturlres","(https?://[^"]+)"',
        response.text,
    )
    if decoded_match:
        return decoded_match.group(1)

    logger.warning("Google News decode response missing publisher URL for %s", source_url)
    return source_url


def _download_image(image_url: str) -> tuple[bytes, str, str] | tuple[None, None, None]:
    try:
        response = requests.get(
            image_url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            stream=True,
        )
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
        if not content_type.startswith("image/"):
            return None, None, None

        data = response.content[: MAX_IMAGE_BYTES + 1]
        if len(data) > MAX_IMAGE_BYTES:
            logger.warning("Skipping oversized image: %s", image_url)
            return None, None, None

        path = urlparse(image_url).path
        filename = os.path.basename(path) or "image.jpg"
        return data, filename, content_type or "image/jpeg"
    except Exception as exc:
        logger.warning("Failed to download image %s: %s", image_url, exc)
        return None, None, None


def _request_with_retries(
    method: str,
    url: str,
    *,
    headers: Optional[dict[str, str]] = None,
    **kwargs,
) -> Response:
    merged_headers = {"User-Agent": USER_AGENT}
    if headers:
        merged_headers.update(headers)

    last_error: Exception | None = None
    for attempt, delay in enumerate((0, *REQUEST_RETRY_DELAYS), start=1):
        if delay:
            time.sleep(delay)
        try:
            response = requests.request(
                method,
                url,
                headers=merged_headers,
                timeout=REQUEST_TIMEOUT,
                **kwargs,
            )
            if response.status_code in {429, 500, 502, 503, 504}:
                response.raise_for_status()
            response.raise_for_status()
            return response
        except requests.HTTPError as exc:
            last_error = exc
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code not in {429, 500, 502, 503, 504} or attempt > len(REQUEST_RETRY_DELAYS):
                raise
            logger.warning(
                "Retrying %s %s after HTTP %s (attempt %s)",
                method,
                url,
                status_code,
                attempt,
            )
        except requests.RequestException as exc:
            last_error = exc
            if attempt > len(REQUEST_RETRY_DELAYS):
                raise
            logger.warning(
                "Retrying %s %s after request error %s (attempt %s)",
                method,
                url,
                exc,
                attempt,
            )

    if last_error:
        raise last_error
    raise RuntimeError(f"Request failed without response: {method} {url}")


def _fetch_article_html(url: str) -> tuple[str, Optional[str]]:
    resolved_url = _decode_google_news_url(url)
    response = requests.get(
        resolved_url,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
        allow_redirects=True,
    )
    response.raise_for_status()
    return response.text, response.url


def _fetch_article_assets(source_url: Optional[str], entry: Optional[dict] = None) -> tuple[Optional[str], Optional[str], tuple[bytes, str, str] | tuple[None, None, None]]:
    if not source_url:
        return None, None, (None, None, None)

    try:
        article_html, resolved_url = _fetch_article_html(source_url)
    except Exception as exc:
        logger.warning("Failed to fetch article page %s: %s", source_url, exc)
        return None, source_url, (None, None, None)

    image_url = _extract_image_url(entry or {}, article_html)
    image_asset = (None, None, None)
    if image_url:
        image_asset = _download_image(image_url)
    return article_html, resolved_url, image_asset


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

    source_url = entry.get("link")
    article_html = None
    if source_url:
        article_html, source_url, image_asset = _fetch_article_assets(source_url, entry)
    else:
        image_asset = (None, None, None)

    summary = _summary_from_entry(entry)
    content = _content_from_summary(summary, source_url or "Unavailable", feed.topic)

    image_data, image_filename, image_mimetype = image_asset

    news = News(
        title=title,
        summary=summary,
        content=content,
        tags=feed.tags,
        published=True,
        slug=slug,
        image_data=image_data,
        image_filename=image_filename,
        image_mimetype=image_mimetype,
    )
    db.add(news)
    db.commit()
    db.refresh(news)
    logger.info("Published automated %s story: %s", feed.topic, title)
    return True


def refresh_automated_article_images(limit: int = 25) -> dict[str, int]:
    stats = {"checked": 0, "updated": 0, "failed": 0}
    db = SessionLocal()
    try:
        recent_news = (
            db.query(News)
            .order_by(News.created_at.desc())
            .limit(limit)
            .all()
        )
        for article in recent_news:
            tags = article.tags or []
            if isinstance(tags, str):
                tags = [tags]
            if "Automation" not in tags:
                continue

            source_url = _extract_source_url_from_content(article.content)
            if not source_url:
                continue

            stats["checked"] += 1
            try:
                _, resolved_url, image_asset = _fetch_article_assets(source_url)
                image_data, image_filename, image_mimetype = image_asset
                if not image_data:
                    continue

                article.image_data = image_data
                article.image_filename = image_filename
                article.image_mimetype = image_mimetype

                if resolved_url and resolved_url != source_url:
                    article.content = re.sub(
                        r"Original source:\s*https?://\S+",
                        f"Original source: {resolved_url}",
                        article.content,
                    )

                db.commit()
                stats["updated"] += 1
                logger.info("Updated automation image for article %s", article.id)
            except Exception as exc:
                db.rollback()
                stats["failed"] += 1
                logger.exception(
                    "Failed to refresh image for article %s: %s",
                    article.id,
                    exc,
                )
    finally:
        db.close()
    return stats


def _iter_entries(feed: FeedConfig, limit: int) -> Iterable[dict]:
    parsed = feedparser.parse(feed.url)
    if parsed.bozo:
        logger.warning("Feed parser warning for %s: %s", feed.url, parsed.bozo_exception)
    return parsed.entries[:limit]


def run_auto_publish(max_per_topic: int = 5) -> dict[str, int]:
    stats = {"ai": 0, "sports": 0}
    db = SessionLocal()
    try:
        for feed in FEEDS:
            if stats.get(feed.topic, 0) >= max_per_topic:
                continue
            for entry in _iter_entries(feed, max_per_topic):
                if stats.get(feed.topic, 0) >= max_per_topic:
                    break
                try:
                    created = _create_news_item(db, feed, entry)
                except Exception as exc:
                    db.rollback()
                    logger.exception(
                        "Auto-publish failed for topic %s and entry %s: %s",
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
