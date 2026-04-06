"""
CrewAI-powered news pipeline.

Architecture
------------
Phase 1 – Discovery (plain Python, deterministic)
  NewsDiscoveryAgent  →  list[DiscoveredNews]   (DuckDuckGo News, no LLM)

Phase 2 – Processing (CrewAI crew, per article)
  ContentWriterAgent  →  fetches source HTML, writes polished article (LLM)
  ImageResearcherAgent →  finds specific, high-quality image (LLM + DDG + Wikipedia)

Phase 3 – Persistence (plain Python, deterministic)
  Save article + image to database via SQLAlchemy

Why CrewAI?
  • Role / goal / backstory dramatically improves GPT output quality
  • Tools are first-class: agents decide HOW and WHEN to call them
  • Sequential Process wires the pipeline with context passing
  • Built-in retry + max_iter guards against runaway LLM loops
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import News, generate_slug
from .auto_publish import (
    StoryDraft,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    _download_image,
    _fetch_article_assets,
    _fetch_wikipedia_image,
    _generate_unique_slug,
    _source_exists,
    _story_exists,
    _clean_title,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Topic buckets – DDG picks the sources, no RSS feeds needed
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
# Data types
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class DiscoveredNews:
    title: str
    url: str
    body: str       # DDG snippet
    source: str     # publication name
    topic: str
    tags: list[str]


class ArticleOutput(BaseModel):
    """Structured output expected from the ContentWriter agent."""
    title: str
    summary: str
    content: str


# ──────────────────────────────────────────────────────────────────────────────
# CrewAI Tools
# ──────────────────────────────────────────────────────────────────────────────

class ArticleFetcherTool(BaseTool):
    name: str = "fetch_article"
    description: str = (
        "Fetches the full text content of a news article from its URL. "
        "Pass the article URL as input. Returns the article body text."
    )

    def _run(self, url: str) -> str:
        try:
            html, resolved_url, _ = _fetch_article_assets(url.strip())
            if not html:
                return "Could not fetch article content."
            # Return plain text (BeautifulSoup strips HTML for the LLM)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            return text[:6000]  # cap to avoid token overflow
        except Exception as exc:
            logger.warning("[ArticleFetcherTool] failed for %s: %s", url, exc)
            return "Could not fetch article content."


class DDGImageSearchTool(BaseTool):
    name: str = "search_image_ddg"
    description: str = (
        "Search DuckDuckGo Images for a news-relevant photo. "
        "Input should be a specific 3-6 word query using person names, "
        "team names, or product names — not generic words like 'news'. "
        "Returns a direct image URL or empty string."
    )

    def _run(self, query: str) -> str:
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                hits = list(
                    ddgs.images(
                        query.strip(),
                        max_results=15,
                        safesearch="off",
                        type_image="photo",
                    )
                )
            for hit in hits:
                img_url = hit.get("image", "")
                if not img_url or not img_url.startswith("http"):
                    continue
                w = hit.get("width") or 0
                h = hit.get("height") or 0
                if (w and w < 400) or (h and h < 300):
                    continue
                logger.info("[DDGImageSearchTool] found: %s", img_url)
                return img_url
        except Exception as exc:
            logger.warning("[DDGImageSearchTool] failed for '%s': %s", query, exc)
        return ""


class WikipediaImageTool(BaseTool):
    name: str = "search_image_wikipedia"
    description: str = (
        "Get the main image from a Wikipedia article. "
        "Use this as a fallback when DDG image search returns nothing. "
        "Input should be the topic or person name to search on Wikipedia. "
        "Returns a direct image URL or empty string."
    )

    def _run(self, topic: str) -> str:
        try:
            url = _fetch_wikipedia_image(topic.strip(), [])
            return url or ""
        except Exception as exc:
            logger.warning("[WikipediaImageTool] failed for '%s': %s", topic, exc)
        return ""


# ──────────────────────────────────────────────────────────────────────────────
# Phase 1 – News Discovery (plain Python, deterministic, no LLM cost)
# ──────────────────────────────────────────────────────────────────────────────

class NewsDiscoveryAgent:
    """
    Searches DuckDuckGo News for each topic bucket.
    No LLM involved – this is fast, cheap, and deterministic.
    """

    def run(self, max_per_bucket: int = 5) -> list[DiscoveredNews]:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            logger.error("duckduckgo-search not installed. Run: pip install duckduckgo-search")
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
                            region="in-en",
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

                logger.info("[Discovery] topic='%s' found=%d", bucket["topic"], len(bucket_results))
                results.extend(bucket_results)
                time.sleep(1.5)

            except Exception as exc:
                logger.warning("[Discovery] topic='%s' failed: %s", bucket["topic"], exc)

        return results


# ──────────────────────────────────────────────────────────────────────────────
# Phase 2 – CrewAI crew: ContentWriter + ImageResearcher
# ──────────────────────────────────────────────────────────────────────────────

def _build_llm() -> LLM:
    return LLM(
        model=f"openai/{OPENAI_MODEL}",
        api_key=OPENAI_API_KEY,
        temperature=0.5,
    )


def _run_article_crew(item: DiscoveredNews) -> tuple[Optional[ArticleOutput], Optional[str]]:
    """
    Run a two-agent CrewAI crew for one article.

    Returns
    -------
    (ArticleOutput, image_url) or (None, None) on failure.
    image_url may be None if no image was found.
    """
    llm = _build_llm()

    # ── Agents ──────────────────────────────────────────────────────────────

    content_writer = Agent(
        role="Senior News Journalist",
        goal=(
            "Write accurate, engaging, and well-structured news articles "
            "for TheCloudMind — an AI-powered Indian news platform."
        ),
        backstory=(
            "You are an experienced journalist with 10+ years covering AI and sports. "
            "You always fetch the original source before writing, and you produce "
            "professional articles with a clear headline, concise summary, and "
            "detailed body that keeps readers engaged. "
            "You never plagiarise — you rephrase and add analysis."
        ),
        tools=[ArticleFetcherTool()],
        llm=llm,
        verbose=False,
        max_iter=3,
        allow_delegation=False,
    )

    image_researcher = Agent(
        role="Visual Content Researcher",
        goal=(
            "Find the single most relevant, high-quality image for each news article. "
            "Use specific entity names — never generic search terms."
        ),
        backstory=(
            "You source images for a professional news platform. "
            "For cricket stories you search by player or team name. "
            "For AI/tech stories you search by company or product name. "
            "You try DuckDuckGo first, then Wikipedia as a fallback."
        ),
        tools=[DDGImageSearchTool(), WikipediaImageTool()],
        llm=llm,
        verbose=False,
        max_iter=3,
        allow_delegation=False,
    )

    # ── Tasks ────────────────────────────────────────────────────────────────

    write_task = Task(
        description=(
            f"Write a full news article about the following story.\n\n"
            f"Headline: {item.title}\n"
            f"Source URL: {item.url}\n"
            f"Snippet: {item.body}\n"
            f"Topic: {item.topic}\n\n"
            "Instructions:\n"
            "1. Fetch the full article from the source URL using the fetch_article tool.\n"
            "2. Write a refined, professional title (can improve the headline).\n"
            "3. Write a 2-3 sentence summary capturing the key news.\n"
            "4. Write the full article content (400-600 words) in clear paragraphs.\n"
            "   - Use <p> tags for each paragraph in the content field.\n"
            "   - Add your own analysis where relevant.\n"
            "   - Do not include any image tags, ads, or navigation text.\n"
        ),
        expected_output=(
            "A JSON object with exactly three fields:\n"
            '{\n'
            '  "title": "The refined article title",\n'
            '  "summary": "2-3 sentence summary of the story",\n'
            '  "content": "<p>Paragraph one...</p><p>Paragraph two...</p>"\n'
            '}'
        ),
        agent=content_writer,
        output_pydantic=ArticleOutput,
    )

    image_task = Task(
        description=(
            f"Find a relevant, high-quality image for this news article.\n\n"
            f"Title: {item.title}\n"
            f"Topic: {item.topic}\n\n"
            "Instructions:\n"
            "1. Extract the most specific entity names from the title "
            "(player name, team, company, AI model).\n"
            "2. Search DuckDuckGo Images using a 3-5 word specific query.\n"
            "3. If DDG returns nothing useful, try Wikipedia with the main topic name.\n"
            "4. Return only the direct image URL (starting with http). "
            "Return 'none' if nothing is found.\n"
        ),
        expected_output=(
            "A single direct image URL starting with 'http', or the string 'none'."
        ),
        agent=image_researcher,
        context=[write_task],
    )

    # ── Crew ─────────────────────────────────────────────────────────────────

    crew = Crew(
        agents=[content_writer, image_researcher],
        tasks=[write_task, image_task],
        process=Process.sequential,
        verbose=False,
    )

    try:
        crew.kickoff()

        # Parse article output
        article_out: ArticleOutput = write_task.output.pydantic
        if not article_out:
            # Fallback: try parsing raw JSON
            import json
            raw = write_task.output.raw or "{}"
            data = json.loads(raw)
            article_out = ArticleOutput(**data)

        # Parse image URL
        image_url_raw = (image_task.output.raw or "").strip()
        image_url = image_url_raw if image_url_raw.startswith("http") else None

        return article_out, image_url

    except Exception as exc:
        logger.exception("[CrewAI] crew failed for '%s': %s", item.title, exc)
        return None, None


# ──────────────────────────────────────────────────────────────────────────────
# Phase 3 – Database persistence
# ──────────────────────────────────────────────────────────────────────────────

def _persist(
    db: Session,
    article: ArticleOutput,
    source_url: str,
    tags: list[str],
    image_data: Optional[bytes],
    image_filename: Optional[str],
    image_mimetype: Optional[str],
) -> bool:
    if _source_exists(db, source_url):
        logger.info("[Persist] skipping existing source: %s", source_url)
        return False

    base_slug = generate_slug(article.title)
    if _story_exists(db, article.title, base_slug):
        logger.info("[Persist] skipping existing title: %s", article.title)
        return False

    news = News(
        title=_clean_title(article.title),
        summary=article.summary,
        content=article.content,
        tags=tags,
        published=True,
        slug=_generate_unique_slug(db, article.title),
        image_data=image_data,
        image_filename=image_filename,
        image_mimetype=image_mimetype,
    )
    db.add(news)
    db.commit()
    db.refresh(news)
    logger.info("[Persist] published: %s", article.title)
    return True


# ──────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ──────────────────────────────────────────────────────────────────────────────

class AgentOrchestrator:
    """
    Coordinates the full pipeline:
      Discovery → CrewAI (write + image) → DB save
    """

    def run(self, max_per_topic: int = 5) -> dict[str, int]:
        if not OPENAI_API_KEY:
            logger.error("[Orchestrator] OPENAI_API_KEY not set — aborting.")
            return {"discovered": 0, "published": 0, "skipped": 0, "failed": 0}

        stats: dict[str, int] = {
            "discovered": 0,
            "published": 0,
            "skipped": 0,
            "failed": 0,
        }

        # Phase 1: Discover news
        items = NewsDiscoveryAgent().run(max_per_bucket=max_per_topic)
        stats["discovered"] = len(items)
        logger.info("[Orchestrator] discovered %d articles", len(items))

        db = SessionLocal()
        topic_counts: dict[str, int] = {}

        try:
            for item in items:
                if topic_counts.get(item.topic, 0) >= max_per_topic:
                    continue

                # Skip if source already in DB (fast check before LLM spend)
                if _source_exists(db, item.url):
                    stats["skipped"] += 1
                    continue

                logger.info("[Orchestrator] processing '%s' (%s)", item.title, item.topic)

                try:
                    # Phase 2: CrewAI crew → article + image URL
                    article_out, image_url = _run_article_crew(item)

                    if article_out is None:
                        stats["failed"] += 1
                        continue

                    # Download image bytes if we got a URL
                    img_data, img_fname, img_mime = None, None, None
                    if image_url:
                        img_data, img_fname, img_mime = _download_image(image_url)

                    # Phase 3: Persist to DB
                    saved = _persist(
                        db, article_out, item.url, item.tags,
                        img_data, img_fname, img_mime,
                    )

                    if saved:
                        stats["published"] += 1
                        topic_counts[item.topic] = topic_counts.get(item.topic, 0) + 1
                    else:
                        stats["skipped"] += 1

                    time.sleep(2)  # respect external services

                except Exception as exc:
                    db.rollback()
                    stats["failed"] += 1
                    logger.exception(
                        "[Orchestrator] pipeline error for '%s': %s", item.title, exc
                    )

        finally:
            db.close()

        logger.info("[Orchestrator] run complete: %s", stats)
        return stats


# ──────────────────────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────────────────────

def run_agent_pipeline(max_per_topic: int = 5) -> dict[str, int]:
    """Run the full CrewAI news pipeline and return stats."""
    return AgentOrchestrator().run(max_per_topic=max_per_topic)
