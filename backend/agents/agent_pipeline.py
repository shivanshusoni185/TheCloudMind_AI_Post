"""
Agent-based news pipeline.

Flow:
  NewsDiscoveryAgent  →  ContentWriterAgent  →  ImageFinderAgent  →  save to DB

* No hardcoded RSS feeds or source names.
* DuckDuckGo News  – discovers what is trending right now.
* DuckDuckGo Images – finds a visually-relevant photo for every article.
* GPT (optional)   – extracts a precise image-search query from the headline.
* Wikipedia        – final image fallback.
"""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Optional

import requests
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import News, generate_slug
from .auto_publish import (
    FeedConfig,
    StoryDraft,
    USER_AGENT,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_CHAT_COMPLETIONS_URL,
    _build_story_from_source,
    _clean_title,
    _download_image,
    _fetch_article_assets,
    _fetch_wikipedia_image,
    _generate_unique_slug,
    _source_exists,
    _story_exists,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Broad topic buckets the agent searches.  No source names – DDG picks them.
# ──────────────────────────────────────────────────────────────────────────────
_TOPIC_BUCKETS: list[dict] = [
    {
        "query": "artificial intelligence machine learning technology 2025",
        "topic": "ai",
        "tags": ["AI", "Technology", "Automation", "Analysis"],
    },
    {
        "query": "IPL 2025 cricket match highlights",
        "topic": "cricket",
        "tags": ["Cricket", "IPL", "Sports", "Automation", "Analysis"],
    },
    {
        "query": "India cricket team latest news 2025",
        "topic": "cricket",
        "tags": ["Cricket", "Sports", "Automation", "Analysis"],
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class DiscoveredNews:
    title: str
    url: str
    body: str          # snippet from DDG
    source: str        # publication name returned by DDG
    topic: str
    tags: list[str]


# ──────────────────────────────────────────────────────────────────────────────
# Agent 1 – NewsDiscoveryAgent
# ──────────────────────────────────────────────────────────────────────────────

class NewsDiscoveryAgent:
    """
    Searches DuckDuckGo News for each topic bucket and returns a flat list
    of DiscoveredNews items.  Works with any trending topic – no feeds needed.
    """

    def run(self, max_per_bucket: int = 5) -> list[DiscoveredNews]:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            logger.error(
                "duckduckgo-search is not installed. "
                "Add it to requirements.txt and run: pip install duckduckgo-search"
            )
            return []

        results: list[DiscoveredNews] = []
        seen_urls: set[str] = set()

        for bucket in _TOPIC_BUCKETS:
            bucket_results: list[DiscoveredNews] = []
            try:
                with DDGS() as ddgs:
                    raw = list(
                        ddgs.news(
                            bucket["query"],
                            max_results=max_per_bucket * 3,
                            region="in-en",   # India / English
                            safesearch="off",
                        )
                    )

                for item in raw:
                    url = item.get("url", "").strip()
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    bucket_results.append(
                        DiscoveredNews(
                            title=item.get("title", "").strip(),
                            url=url,
                            body=item.get("body", "").strip(),
                            source=item.get("source", "").strip(),
                            topic=bucket["topic"],
                            tags=list(bucket["tags"]),
                        )
                    )
                    if len(bucket_results) >= max_per_bucket:
                        break

                logger.info(
                    "[NewsDiscoveryAgent] topic='%s'  found=%d",
                    bucket["topic"], len(bucket_results),
                )
                results.extend(bucket_results)
                time.sleep(1.5)  # DDG rate-limit courtesy

            except Exception as exc:
                logger.warning(
                    "[NewsDiscoveryAgent] topic='%s' failed: %s",
                    bucket["topic"], exc,
                )

        return results


# ──────────────────────────────────────────────────────────────────────────────
# Agent 2 – ImageFinderAgent
# ──────────────────────────────────────────────────────────────────────────────

class ImageFinderAgent:
    """
    Finds a contextually-relevant image for an article.

    Steps
    -----
    1. Ask GPT to extract a *specific* image-search query from the headline
       (e.g. "MS Dhoni batting CSK" instead of generic "cricket player").
    2. Search DuckDuckGo Images with that query.
    3. Download the first valid photo.
    4. Fall back to Wikipedia if DDG returns nothing.
    """

    # ── query builder ──────────────────────────────────────────────────────

    def _gpt_image_query(self, title: str, summary: str) -> str:
        """Use GPT to produce a precise, specific image-search query."""
        if not OPENAI_API_KEY:
            return ""

        prompt = (
            "You are an image researcher. Given a news headline, output a "
            "3–6 word image search query that will find a visually relevant "
            "photo on the internet.\n\n"
            "Rules:\n"
            "• Use the most specific person name, team name, or product name present.\n"
            "• Cricket headlines → include the player's full name and/or team name.\n"
            "• AI/tech headlines → include the company or model name.\n"
            "• Never use generic words like 'news', 'latest', 'report', 'update'.\n"
            "• Output ONLY the query — no quotes, no explanation.\n\n"
            f"Headline: {title}\n"
            f"Summary: {summary[:200]}"
        )

        try:
            resp = requests.post(
                OPENAI_CHAT_COMPLETIONS_URL,
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENAI_MODEL,
                    "temperature": 0.1,
                    "max_tokens": 30,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=10,
            )
            resp.raise_for_status()
            query = resp.json()["choices"][0]["message"]["content"].strip().strip("\"'")
            if query and len(query) > 3:
                logger.info("[ImageFinderAgent] GPT query: '%s'", query)
                return query
        except Exception as exc:
            logger.warning("[ImageFinderAgent] GPT query failed: %s", exc)
        return ""

    def _heuristic_image_query(self, title: str, topic: str) -> str:
        """
        No-API fallback: groups consecutive capitalised tokens into named
        entities and picks the two most specific ones.
        """
        tokens = re.findall(r"\S+", title)
        entities: list[str] = []
        current: list[str] = []
        for tok in tokens:
            clean = re.sub(r"[^\w]", "", tok)
            if clean and clean[0].isupper():
                current.append(clean)
            else:
                if current:
                    entities.append(" ".join(current))
                current = []
        if current:
            entities.append(" ".join(current))

        entities.sort(key=lambda e: -len(e))
        parts = [e for e in entities if len(e.replace(" ", "")) > 2][:2]
        if topic and topic.lower() not in " ".join(parts).lower():
            parts.append(topic)
        return " ".join(parts[:3])

    def _build_query(self, title: str, summary: str, topic: str) -> str:
        q = self._gpt_image_query(title, summary)
        return q if q else self._heuristic_image_query(title, topic)

    # ── DDG image search ───────────────────────────────────────────────────

    def _ddg_image_search(self, query: str) -> Optional[str]:
        """Return the URL of the first suitable image from DuckDuckGo."""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return None

        try:
            with DDGS() as ddgs:
                hits = list(
                    ddgs.images(
                        query,
                        max_results=15,
                        safesearch="off",
                        type_image="photo",
                    )
                )

            for hit in hits:
                img_url = hit.get("image", "")
                if not img_url or not img_url.startswith("http"):
                    continue
                # Skip tiny images (icons / thumbnails)
                w = hit.get("width") or 0
                h = hit.get("height") or 0
                if (w and w < 400) or (h and h < 300):
                    continue
                logger.info(
                    "[ImageFinderAgent] DDG image for '%s': %s", query, img_url
                )
                return img_url

        except Exception as exc:
            logger.warning(
                "[ImageFinderAgent] DDG image search failed for '%s': %s", query, exc
            )
        return None

    # ── public API ─────────────────────────────────────────────────────────

    def run(
        self,
        title: str,
        summary: str,
        topic: str,
        tags: list[str],
    ) -> tuple[bytes, str, str] | tuple[None, None, None]:
        """
        Return (image_bytes, filename, mimetype) or (None, None, None).
        """
        query = self._build_query(title, summary, topic)
        logger.info("[ImageFinderAgent] searching: '%s'", query)

        # 1. DuckDuckGo images
        img_url = self._ddg_image_search(query)
        if img_url:
            data, fname, mime = _download_image(img_url)
            if data:
                return data, fname, mime

        # 2. Wikipedia fallback
        wiki_url = _fetch_wikipedia_image(title, tags)
        if wiki_url:
            data, fname, mime = _download_image(wiki_url)
            if data:
                return data, fname, mime

        logger.warning("[ImageFinderAgent] no image found for '%s'", title)
        return None, None, None


# ──────────────────────────────────────────────────────────────────────────────
# Agent 3 – ContentWriterAgent
# ──────────────────────────────────────────────────────────────────────────────

class ContentWriterAgent:
    """
    Fetches the full article page and uses OpenAI (or rule-based fallback) to
    write a professional news analysis article.
    """

    def run(
        self, item: DiscoveredNews
    ) -> Optional[tuple[StoryDraft, str]]:
        """
        Returns (StoryDraft, resolved_source_url) or None on hard failure.
        """
        feed = FeedConfig(
            topic=item.topic,
            source_name=item.source or "News",
            url="",
            tags=item.tags,
        )

        try:
            article_html, resolved_url, _ = _fetch_article_assets(item.url)
            source_url = resolved_url or item.url
        except Exception as exc:
            logger.warning(
                "[ContentWriterAgent] fetch failed for %s: %s", item.url, exc
            )
            source_url = item.url
            article_html = None

        draft = _build_story_from_source(
            feed=feed,
            source_url=source_url,
            source_title=item.title,
            source_summary=item.body,
            article_html=article_html,
        )
        return draft, source_url


# ──────────────────────────────────────────────────────────────────────────────
# AgentOrchestrator
# ──────────────────────────────────────────────────────────────────────────────

class AgentOrchestrator:
    """
    Coordinates all agents and persists results to the database.

    Pipeline per article
    --------------------
    NewsDiscoveryAgent → ContentWriterAgent → ImageFinderAgent → DB save
    """

    def __init__(self) -> None:
        self.discovery = NewsDiscoveryAgent()
        self.writer = ContentWriterAgent()
        self.image_finder = ImageFinderAgent()

    def _persist(
        self,
        db: Session,
        draft: StoryDraft,
        source_url: str,
        tags: list[str],
        image_data: Optional[bytes],
        image_filename: Optional[str],
        image_mimetype: Optional[str],
    ) -> bool:
        if _source_exists(db, source_url):
            logger.info("Skipping existing source: %s", source_url)
            return False

        base_slug = generate_slug(draft.title)
        if _story_exists(db, draft.title, base_slug):
            logger.info("Skipping existing title: %s", draft.title)
            return False

        news = News(
            title=draft.title,
            summary=draft.summary,
            content=draft.content,
            tags=tags,
            published=True,
            slug=_generate_unique_slug(db, draft.title),
            image_data=image_data,
            image_filename=image_filename,
            image_mimetype=image_mimetype,
        )
        db.add(news)
        db.commit()
        db.refresh(news)
        logger.info("[AgentOrchestrator] published: %s", draft.title)
        return True

    def run(self, max_per_topic: int = 5) -> dict[str, int]:
        stats: dict[str, int] = {
            "discovered": 0,
            "published": 0,
            "skipped": 0,
            "failed": 0,
        }
        db = SessionLocal()
        topic_counts: dict[str, int] = {}

        try:
            items = self.discovery.run(max_per_bucket=max_per_topic)
            stats["discovered"] = len(items)

            for item in items:
                # Respect per-topic cap
                if topic_counts.get(item.topic, 0) >= max_per_topic:
                    continue

                logger.info(
                    "[AgentOrchestrator] processing '%s' (%s)",
                    item.title, item.topic,
                )

                try:
                    # Step 1 – write content
                    result = self.writer.run(item)
                    if result is None:
                        stats["failed"] += 1
                        continue
                    draft, source_url = result

                    # Step 2 – find image
                    img_data, img_fname, img_mime = self.image_finder.run(
                        title=draft.title,
                        summary=draft.summary,
                        topic=item.topic,
                        tags=item.tags,
                    )

                    # Step 3 – persist
                    saved = self._persist(
                        db, draft, source_url, item.tags,
                        img_data, img_fname, img_mime,
                    )

                    if saved:
                        stats["published"] += 1
                        topic_counts[item.topic] = topic_counts.get(item.topic, 0) + 1
                    else:
                        stats["skipped"] += 1

                    time.sleep(2)  # Respect external services

                except Exception as exc:
                    db.rollback()
                    stats["failed"] += 1
                    logger.exception(
                        "[AgentOrchestrator] pipeline error for '%s': %s",
                        item.title, exc,
                    )

        finally:
            db.close()

        logger.info("[AgentOrchestrator] run complete: %s", stats)
        return stats


# ──────────────────────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────────────────────

def run_agent_pipeline(max_per_topic: int = 5) -> dict[str, int]:
    """Run the full agent pipeline and return stats."""
    return AgentOrchestrator().run(max_per_topic=max_per_topic)
