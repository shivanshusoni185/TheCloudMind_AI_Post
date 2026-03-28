import html
import json
import logging
import os
import re
import time
import unicodedata
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
MAX_SOURCE_CHARS = 6000
MAX_BODY_PARAGRAPHS = 8
MIN_PARAGRAPH_LENGTH = 60
USER_AGENT = (
    "Mozilla/5.0 (compatible; TheCloudMindBot/2.0; "
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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
OPENAI_CHAT_COMPLETIONS_URL = os.getenv(
    "OPENAI_CHAT_COMPLETIONS_URL",
    "https://api.openai.com/v1/chat/completions",
).strip()
SOURCE_NAME_MAP = {
    "techcrunch.com": "TechCrunch",
    "www.theverge.com": "The Verge",
    "theverge.com": "The Verge",
    "www.marktechpost.com": "MarkTechPost",
    "marktechpost.com": "MarkTechPost",
    "www.espn.com": "ESPN",
    "espn.com": "ESPN",
    "sportstar.thehindu.com": "Sportstar",
    "www.cbssports.com": "CBS Sports",
    "cbssports.com": "CBS Sports",
}


@dataclass(frozen=True)
class FeedConfig:
    topic: str
    source_name: str
    url: str
    tags: list[str]


@dataclass(frozen=True)
class StoryDraft:
    title: str
    summary: str
    content: str


FEEDS: tuple[FeedConfig, ...] = (
    FeedConfig(
        topic="ai",
        source_name="TechCrunch",
        url="https://techcrunch.com/category/artificial-intelligence/feed/",
        tags=["AI", "Automation", "Analysis"],
    ),
    FeedConfig(
        topic="ai",
        source_name="The Verge",
        url="https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        tags=["AI", "Automation", "Analysis"],
    ),
    FeedConfig(
        topic="ai",
        source_name="MarkTechPost",
        url="https://www.marktechpost.com/feed/",
        tags=["AI", "Automation", "Analysis"],
    ),
    FeedConfig(
        topic="sports",
        source_name="ESPN",
        url="https://www.espn.com/espn/rss/news",
        tags=["Sports", "Automation", "Analysis"],
    ),
    FeedConfig(
        topic="sports",
        source_name="Sportstar",
        url="https://sportstar.thehindu.com/feeder/default.rss",
        tags=["Sports", "Automation", "Analysis"],
    ),
    FeedConfig(
        topic="sports",
        source_name="CBS Sports",
        url="https://www.cbssports.com/rss/headlines/",
        tags=["Sports", "Automation", "Analysis"],
    ),
)


def _repair_mojibake(value: str) -> str:
    if not value:
        return ""
    repaired = value
    try:
        candidate = repaired.encode("latin1").decode("utf-8")
        if candidate and candidate != repaired:
            repaired = candidate
    except Exception:
        pass
    return unicodedata.normalize("NFKC", repaired)


def _clean_text(value: str) -> str:
    text = BeautifulSoup(html.unescape(value or ""), "html.parser").get_text(" ")
    text = _repair_mojibake(text)
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
    return ""


def _extract_meta_description(article_html: Optional[str]) -> str:
    if not article_html:
        return ""
    soup = BeautifulSoup(article_html, "html.parser")
    selectors = [
        ("meta", {"name": "description"}),
        ("meta", {"property": "og:description"}),
        ("meta", {"name": "twitter:description"}),
    ]
    for tag_name, attrs in selectors:
        tag = soup.find(tag_name, attrs=attrs)
        if tag and tag.get("content"):
            cleaned = _clean_text(tag["content"])
            if cleaned:
                return cleaned[:500]
    return ""


def _is_noise_paragraph(text: str) -> bool:
    lowered = text.lower()
    noise_patterns = (
        "cookie",
        "newsletter",
        "sign up",
        "subscribe",
        "all rights reserved",
        "advertisement",
        "privacy policy",
        "terms of use",
        "follow us",
        "read more",
        "listen to article",
    )
    return len(text) < MIN_PARAGRAPH_LENGTH or any(pattern in lowered for pattern in noise_patterns)


def _extract_article_text(article_html: Optional[str]) -> str:
    if not article_html:
        return ""

    soup = BeautifulSoup(article_html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "form", "aside"]):
        tag.decompose()

    paragraph_candidates: list[str] = []
    selectors = [
        "article p",
        "main p",
        "[role='main'] p",
        ".article-content p",
        ".story-body p",
        ".entry-content p",
        ".c-entry-content p",
        ".post-content p",
        ".post-body p",
        ".content p",
        "p",
    ]

    for selector in selectors:
        for node in soup.select(selector):
            text = _clean_text(node.get_text(" ", strip=True))
            if not text or _is_noise_paragraph(text):
                continue
            if text not in paragraph_candidates:
                paragraph_candidates.append(text)
        if len(paragraph_candidates) >= MAX_BODY_PARAGRAPHS:
            break

    excerpt = []
    total_chars = 0
    for paragraph in paragraph_candidates:
        if total_chars + len(paragraph) > MAX_SOURCE_CHARS:
            break
        excerpt.append(paragraph)
        total_chars += len(paragraph)
        if len(excerpt) >= MAX_BODY_PARAGRAPHS:
            break

    return "\n\n".join(excerpt)


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
    return parsed.netloc.lower() in PLACEHOLDER_IMAGE_HOSTS


def _extract_source_url_from_content(content: str) -> Optional[str]:
    match = re.search(r"Original source:\s*(https?://\S+)", content or "")
    return match.group(1).strip() if match else None


def _extract_source_name_from_url(url: str, fallback: str = "") -> str:
    host = urlparse(url).netloc.lower()
    if host in SOURCE_NAME_MAP:
        return SOURCE_NAME_MAP[host]
    if fallback:
        return fallback
    host = host.replace("www.", "")
    stem = host.split(".")[0] if host else "Source"
    return stem.replace("-", " ").title()


def _decode_google_news_url(source_url: str) -> str:
    parsed = urlparse(source_url)
    if parsed.netloc not in GOOGLE_NEWS_HOSTS or "/rss/articles/" not in parsed.path:
        return source_url

    article_id = parsed.path.rstrip("/").split("/")[-1]
    article_page = _request_with_retries("GET", f"https://news.google.com/articles/{article_id}")

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
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
    )

    decoded_match = re.search(r'\["garturlres","(https?://[^"]+)"', response.text)
    if decoded_match:
        return decoded_match.group(1)

    logger.warning("Google News decode response missing publisher URL for %s", source_url)
    return source_url


def _download_image(image_url: str) -> tuple[bytes, str, str] | tuple[None, None, None]:
    try:
        response = _request_with_retries("GET", image_url, stream=True)
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
    response = _request_with_retries("GET", resolved_url, allow_redirects=True)
    return response.text, response.url


def _fetch_article_assets(
    source_url: Optional[str],
    entry: Optional[dict] = None,
) -> tuple[Optional[str], Optional[str], tuple[bytes, str, str] | tuple[None, None, None]]:
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


def _source_exists(db: Session, source_url: str) -> bool:
    return db.query(News.id).filter(News.content.ilike(f"%Original source: {source_url}%")).first() is not None


def _story_exists(db: Session, title: str, base_slug: str) -> bool:
    return db.query(News.id).filter(or_(News.title == title, News.slug == base_slug)).first() is not None


def _generate_unique_slug(db: Session, title: str, current_id: Optional[int] = None) -> str:
    slug = generate_slug(title)
    candidate = slug
    counter = 2
    while True:
        query = db.query(News.id).filter(News.slug == candidate)
        if current_id is not None:
            query = query.filter(News.id != current_id)
        if query.first() is None:
            return candidate
        candidate = f"{slug}-{counter}"
        counter += 1


def _format_content(sections: list[tuple[str, str]], source_name: str, source_url: str) -> str:
    blocks = []
    for heading, body in sections:
        cleaned = _clean_text(body)
        if not cleaned:
            continue
        blocks.append(f"## {heading}\n{cleaned}")
    blocks.append(f"Source note: Adapted from reporting by {source_name}.")
    blocks.append(f"Original source: {source_url}")
    return "\n\n".join(blocks)


def _fallback_story_draft(
    *,
    topic: str,
    source_name: str,
    source_url: str,
    source_title: str,
    source_summary: str,
    article_text: str,
) -> StoryDraft:
    excerpt_parts = [part for part in article_text.split("\n\n") if part.strip()]
    lead = source_summary or (excerpt_parts[0] if excerpt_parts else source_title)
    supporting = excerpt_parts[1] if len(excerpt_parts) > 1 else source_summary or source_title
    context = excerpt_parts[2] if len(excerpt_parts) > 2 else (
        f"This {topic} development is part of a larger shift worth tracking across the sector."
    )
    watch = excerpt_parts[3] if len(excerpt_parts) > 3 else (
        "Watch for official announcements, follow-on disclosures, and market reaction over the next few days."
    )

    sections = [
        ("What happened", lead),
        ("Why it matters", supporting),
        ("Key details", context),
        ("What to watch", watch),
    ]
    summary = _clean_text(source_summary or lead)[:280]
    return StoryDraft(
        title=_clean_title(source_title),
        summary=summary,
        content=_format_content(sections, source_name, source_url),
    )


def _generate_story_draft(
    *,
    topic: str,
    source_name: str,
    source_url: str,
    source_title: str,
    source_summary: str,
    article_text: str,
) -> StoryDraft:
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY is missing; using fallback story draft for %s", source_url)
        return _fallback_story_draft(
            topic=topic,
            source_name=source_name,
            source_url=source_url,
            source_title=source_title,
            source_summary=source_summary,
            article_text=article_text,
        )

    source_context = article_text[:MAX_SOURCE_CHARS] if article_text else source_summary
    if not source_context:
        return _fallback_story_draft(
            topic=topic,
            source_name=source_name,
            source_url=source_url,
            source_title=source_title,
            source_summary=source_summary,
            article_text=article_text,
        )

    system_prompt = (
        "You are the lead editor for TheCloudMind.ai. Rewrite source reporting into an original, "
        "clean news analysis article. Do not copy source phrasing. Be factual, concise, and readable. "
        "Avoid hype, filler, and mentioning AI generation. Return valid JSON only."
    )
    user_prompt = f"""
Create a concise original article for TheCloudMind.ai from the source material below.

Requirements:
- Topic: {topic}
- Audience: professionals and informed general readers
- Use plain English
- Keep the title sharp and publication-ready
- Summary must be 1 to 2 sentences and under 280 characters
- Content must have exactly four sections with these headings:
  1. What happened
  2. Why it matters
  3. Key details
  4. What to watch
- Each section should be one compact paragraph
- Do not repeat the summary inside the first paragraph
- Do not invent facts beyond the source material
- Preserve nuance and uncertainty where needed
- Do not use bullet points
- Do not include markdown beyond the section headings

Return JSON with this shape:
{{
  "title": "...",
  "summary": "...",
  "sections": [
    {{"heading": "What happened", "body": "..."}},
    {{"heading": "Why it matters", "body": "..."}},
    {{"heading": "Key details", "body": "..."}},
    {{"heading": "What to watch", "body": "..."}}
  ]
}}

Source publication: {source_name}
Source title: {source_title}
Source summary: {source_summary}
Source URL: {source_url}
Source excerpt:
{source_context}
""".strip()

    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    try:
        response = _request_with_retries(
            "POST",
            OPENAI_CHAT_COMPLETIONS_URL,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        data = response.json()
        raw_content = data["choices"][0]["message"]["content"]
        parsed = json.loads(raw_content)
        title = _clean_title(parsed.get("title") or source_title)
        summary = _clean_text(parsed.get("summary") or source_summary)[:280]
        raw_sections = parsed.get("sections") or []
        sections = []
        for section in raw_sections:
            heading = _clean_text(section.get("heading", ""))
            body = _clean_text(section.get("body", ""))
            if heading and body:
                sections.append((heading, body))
        if len(sections) != 4:
            raise ValueError("Model returned an unexpected section count")
        content = _format_content(sections, source_name, source_url)
        return StoryDraft(title=title, summary=summary, content=content)
    except Exception as exc:
        logger.warning("OpenAI generation failed for %s: %s", source_url, exc)
        return _fallback_story_draft(
            topic=topic,
            source_name=source_name,
            source_url=source_url,
            source_title=source_title,
            source_summary=source_summary,
            article_text=article_text,
        )


def _build_story_from_source(
    *,
    feed: FeedConfig,
    source_url: str,
    source_title: str,
    source_summary: str,
    article_html: Optional[str],
) -> StoryDraft:
    meta_summary = _extract_meta_description(article_html)
    article_text = _extract_article_text(article_html)
    summary_seed = meta_summary or source_summary
    source_name = _extract_source_name_from_url(source_url, feed.source_name)
    return _generate_story_draft(
        topic=feed.topic,
        source_name=source_name,
        source_url=source_url,
        source_title=source_title,
        source_summary=summary_seed,
        article_text=article_text,
    )


def _create_news_item(db: Session, feed: FeedConfig, entry: dict) -> bool:
    source_title = _clean_title(entry.get("title", ""))
    if not source_title:
        return False

    source_url = entry.get("link")
    article_html = None
    if source_url:
        article_html, source_url, image_asset = _fetch_article_assets(source_url, entry)
    else:
        image_asset = (None, None, None)

    if not source_url:
        logger.warning("Skipping entry without source URL from %s", feed.source_name)
        return False

    if _source_exists(db, source_url):
        logger.info("Skipping existing source story: %s", source_url)
        return False

    draft = _build_story_from_source(
        feed=feed,
        source_url=source_url,
        source_title=source_title,
        source_summary=_summary_from_entry(entry),
        article_html=article_html,
    )

    base_slug = generate_slug(draft.title)
    if _story_exists(db, draft.title, base_slug):
        logger.info("Skipping existing story title: %s", draft.title)
        return False

    image_data, image_filename, image_mimetype = image_asset
    news = News(
        title=draft.title,
        summary=draft.summary,
        content=draft.content,
        tags=feed.tags,
        published=True,
        slug=_generate_unique_slug(db, draft.title),
        image_data=image_data,
        image_filename=image_filename,
        image_mimetype=image_mimetype,
    )
    db.add(news)
    db.commit()
    db.refresh(news)
    logger.info("Published automated %s story from %s: %s", feed.topic, feed.source_name, draft.title)
    return True


def refresh_automated_article_images(limit: int = 25) -> dict[str, int]:
    stats = {"checked": 0, "updated": 0, "failed": 0}
    db = SessionLocal()
    try:
        recent_news = db.query(News).order_by(News.created_at.desc()).limit(limit).all()
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
                _, _, image_asset = _fetch_article_assets(source_url)
                image_data, image_filename, image_mimetype = image_asset
                if not image_data:
                    continue
                article.image_data = image_data
                article.image_filename = image_filename
                article.image_mimetype = image_mimetype
                db.commit()
                stats["updated"] += 1
                logger.info("Updated automation image for article %s", article.id)
            except Exception as exc:
                db.rollback()
                stats["failed"] += 1
                logger.exception("Failed to refresh image for article %s: %s", article.id, exc)
    finally:
        db.close()
    return stats


def refresh_automated_article_content(limit: int = 25) -> dict[str, int]:
    stats = {"checked": 0, "updated": 0, "failed": 0}
    db = SessionLocal()
    try:
        recent_news = db.query(News).order_by(News.created_at.desc()).limit(limit).all()
        for article in recent_news:
            tags = article.tags or []
            if isinstance(tags, str):
                tags = [tags]
            if "Automation" not in tags:
                continue

            source_url = _extract_source_url_from_content(article.content)
            if not source_url:
                continue

            topic = "sports" if "Sports" in tags else "ai"
            feed = FeedConfig(
                topic=topic,
                source_name=_extract_source_name_from_url(source_url),
                url="",
                tags=list(tags),
            )
            stats["checked"] += 1
            try:
                article_html, resolved_url, image_asset = _fetch_article_assets(source_url)
                final_source_url = resolved_url or source_url
                draft = _build_story_from_source(
                    feed=feed,
                    source_url=final_source_url,
                    source_title=article.title,
                    source_summary=article.summary,
                    article_html=article_html,
                )
                article.title = draft.title
                article.summary = draft.summary
                article.content = draft.content
                article.slug = _generate_unique_slug(db, draft.title, current_id=article.id)
                image_data, image_filename, image_mimetype = image_asset
                if image_data:
                    article.image_data = image_data
                    article.image_filename = image_filename
                    article.image_mimetype = image_mimetype
                db.commit()
                stats["updated"] += 1
                logger.info("Regenerated automation content for article %s", article.id)
            except Exception as exc:
                db.rollback()
                stats["failed"] += 1
                logger.exception("Failed to regenerate automation content for article %s: %s", article.id, exc)
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
            for entry in _iter_entries(feed, max_per_topic * 3):
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
