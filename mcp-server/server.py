"""
TheCloudMind.ai MCP server (read-only).

Exposes the public news + jobs data of https://cloudmindai.in as MCP tools so
Claude (Desktop, Code, or a claude.ai custom connector) can browse and search
the site's content.

Transports
----------
- stdio (default): for local use in Claude Desktop / Claude Code.
- streamable-http: for remote hosting behind HTTPS (claude.ai connectors).

Environment
-----------
TCM_API_BASE   Base URL of the public API. Default: https://cloudmindai.in/api
MCP_TRANSPORT  "stdio" (default) or "http".
MCP_HOST       Bind host for http transport. Default: 0.0.0.0
MCP_PORT       Bind port for http transport. Default: 8765
MCP_PATH       URL path for the streamable-http endpoint. Default: /mcp
MCP_AUTH_TOKEN If set (http transport only), clients must send
               `Authorization: Bearer <token>`. Leave empty to disable.

All data served is already public on the website; the token only gates who may
reach the remote MCP endpoint.
"""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP

API_BASE = os.getenv("TCM_API_BASE", "https://cloudmindai.in/api").rstrip("/")
SITE_BASE = API_BASE[:-4] if API_BASE.endswith("/api") else API_BASE
REQUEST_TIMEOUT = 20.0

mcp = FastMCP("thecloudmind")

_client = httpx.Client(
    base_url=API_BASE,
    timeout=REQUEST_TIMEOUT,
    headers={"User-Agent": "TheCloudMind-MCP/1.0"},
    follow_redirects=True,
)


def _get(path: str, params: Optional[dict[str, Any]] = None) -> Any:
    """GET a public API path and return parsed JSON, raising on HTTP errors."""
    resp = _client.get(path, params={k: v for k, v in (params or {}).items() if v not in (None, "")})
    resp.raise_for_status()
    return resp.json()


def _abs_image(url: Optional[str]) -> Optional[str]:
    """Turn a relative image path (e.g. /news/image/12) into an absolute URL."""
    if not url:
        return None
    if url.startswith("http"):
        return url
    return f"{API_BASE}{url}" if url.startswith("/") else f"{API_BASE}/{url}"


def _article_url(slug: str) -> str:
    return f"{SITE_BASE}/news/{slug}"


def _job_url(slug: str) -> str:
    return f"{SITE_BASE}/jobs/{slug}"


def _shape_article_list_item(a: dict) -> dict:
    return {
        "title": a.get("title"),
        "slug": a.get("slug"),
        "summary": a.get("summary"),
        "tags": a.get("tags") or [],
        "published_at": a.get("created_at"),
        "url": _article_url(a.get("slug", "")),
        "image_url": _abs_image(a.get("image_url")),
    }


def _shape_job(j: dict) -> dict:
    return {
        "title": j.get("title"),
        "slug": j.get("slug"),
        "company": j.get("company"),
        "location": j.get("location"),
        "remote": j.get("remote"),
        "job_type": j.get("job_type"),
        "category": j.get("category"),
        "salary": j.get("salary"),
        "tags": j.get("tags") or [],
        "posted_at": j.get("posted_at") or j.get("created_at"),
        "url": _job_url(j.get("slug", "")),
    }


# ── Article tools ───────────────────────────────────────────────────────────

@mcp.tool()
def search_articles(query: str = "", tag: str = "", limit: int = 20) -> dict:
    """Search TheCloudMind.ai news articles.

    Args:
        query: Free-text search matched against title and summary. Empty = all.
        tag: Filter by a single tag, e.g. "AI", "Cricket", "Automation".
        limit: Max articles to return (1-100).

    Returns a dict with `count` and `articles` (title, slug, summary, tags,
    published_at, url, image_url). Use get_article(slug) for full body text.
    """
    limit = max(1, min(limit, 100))
    data = _get("/news", {"search": query, "tag": tag})
    items = [_shape_article_list_item(a) for a in data[:limit]]
    return {"count": len(items), "total_matched": len(data), "articles": items}


@mcp.tool()
def list_recent_articles(limit: int = 10) -> dict:
    """List the most recently published articles (newest first).

    Args:
        limit: How many recent articles to return (1-50).
    """
    limit = max(1, min(limit, 50))
    data = _get("/news")
    items = [_shape_article_list_item(a) for a in data[:limit]]
    return {"count": len(items), "articles": items}


@mcp.tool()
def get_article(slug: str) -> dict:
    """Fetch a single article's full content by its slug.

    Args:
        slug: The article slug, e.g. "openai-launches-new-model".
              Get slugs from search_articles / list_recent_articles.

    Returns the full article including `content` (Markdown body).
    """
    a = _get(f"/news/by-slug/{slug}")
    return {
        "title": a.get("title"),
        "slug": a.get("slug"),
        "summary": a.get("summary"),
        "content": a.get("content"),
        "tags": a.get("tags") or [],
        "published_at": a.get("created_at"),
        "url": _article_url(a.get("slug", "")),
        "image_url": _abs_image(a.get("image_url")),
    }


# ── Job tools ───────────────────────────────────────────────────────────────

@mcp.tool()
def search_jobs(
    query: str = "",
    category: str = "",
    tag: str = "",
    remote_only: bool = False,
    limit: int = 20,
) -> dict:
    """Search the TheCloudMind.ai jobs board.

    Args:
        query: Free-text search (title/company).
        category: Filter by category, e.g. "Software Development",
                  "Artificial Intelligence". Use list_job_categories for options.
        tag: Filter by a single tag.
        remote_only: If true, only remote roles.
        limit: Max jobs to return (1-100).
    """
    limit = max(1, min(limit, 100))
    params: dict[str, Any] = {"search": query, "category": category, "tag": tag}
    if remote_only:
        params["remote"] = "true"
    data = _get("/jobs", params)
    items = [_shape_job(j) for j in data[:limit]]
    return {"count": len(items), "total_matched": len(data), "jobs": items}


@mcp.tool()
def get_job(slug: str) -> dict:
    """Fetch a single job posting's full details by its slug."""
    j = _get(f"/jobs/by-slug/{slug}")
    shaped = _shape_job(j)
    shaped["description"] = j.get("description")
    shaped["apply_url"] = j.get("apply_url") or j.get("url")
    return shaped


@mcp.tool()
def list_job_categories() -> dict:
    """List all available job categories on the board."""
    cats = _get("/jobs/categories")
    return {"categories": cats}


# ── Overview ─────────────────────────────────────────────────────────────────

@mcp.tool()
def get_overview() -> dict:
    """High-level counts for the site: total published articles and open jobs."""
    news = _get("/news")
    jobs = _get("/jobs")
    tag_counts: dict[str, int] = {}
    for a in news:
        for t in (a.get("tags") or []):
            tag_counts[t] = tag_counts.get(t, 0) + 1
    top_tags = dict(sorted(tag_counts.items(), key=lambda kv: -kv[1])[:12])
    return {
        "site": SITE_BASE,
        "published_articles": len(news),
        "open_jobs": len(jobs),
        "top_article_tags": top_tags,
    }


# ── Entrypoint ───────────────────────────────────────────────────────────────

class _BearerAuthASGI:
    """Pure-ASGI bearer-token gate.

    Wraps the FastMCP app at the ASGI layer (not BaseHTTPMiddleware) so that
    (a) the inner app's lifespan/websocket scopes are forwarded untouched — the
    streamable-http session manager needs its lifespan to run — and (b) the SSE
    stream is not buffered. Unauthenticated `/healthz` is allowed for probes.
    """

    def __init__(self, app, token: str) -> None:
        self._app = app
        self._token = token

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            # lifespan, websocket → pass straight through
            await self._app(scope, receive, send)
            return

        from starlette.responses import JSONResponse

        path = scope.get("path", "").rstrip("/")
        if path == "/healthz":
            await JSONResponse({"status": "ok"})(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        auth = headers.get(b"authorization", b"").decode()
        if auth != f"Bearer {self._token}":
            await JSONResponse({"error": "unauthorized"}, status_code=401)(scope, receive, send)
            return

        await self._app(scope, receive, send)


def _run_http() -> None:
    """Run the streamable-http transport, optionally gated by a bearer token."""
    import uvicorn

    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8765"))
    path = os.getenv("MCP_PATH", "/mcp")
    token = os.getenv("MCP_AUTH_TOKEN", "").strip()

    mcp.settings.host = host
    mcp.settings.port = port
    mcp.settings.streamable_http_path = path

    app = mcp.streamable_http_app()
    if token:
        app = _BearerAuthASGI(app, token)

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").strip().lower()
    if transport in ("http", "streamable-http", "streamable_http"):
        _run_http()
    else:
        mcp.run(transport="stdio")
