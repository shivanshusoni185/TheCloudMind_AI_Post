import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .database import engine, Base
from .routers import admin, news, contact
from .scheduler import start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)

# Try to create tables on startup; non-fatal so the process still boots.
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified")
except Exception as exc:
    logger.error("Failed to create database tables: %s", exc)

app = FastAPI(title="AI News API", version="1.0.0")

# ── Middleware ────────────────────────────────────────────────────
# GZip: compress JSON responses > 1 KB (news list can be large).
app.add_middleware(GZipMiddleware, minimum_size=1024)

allowed_origins = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS",
        "https://cloudmindai.in,https://www.cloudmindai.in,https://thecloudmind-web.fly.dev",
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────
app.include_router(admin.router)
app.include_router(news.router)
app.include_router(contact.router)


# ── Lifecycle ─────────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    start_scheduler()


@app.on_event("shutdown")
async def on_shutdown():
    stop_scheduler()


# ── Root / Health ─────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"message": "AI News API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """
    Lightweight health check used by Fly.io probes.

    Opens one synchronous connection to verify DB reachability, but runs
    inside a thread so it does not block the async event loop.
    """
    import asyncio
    from .database import engine as _engine

    def _ping():
        try:
            conn = _engine.connect()
            conn.close()
            return "connected"
        except Exception as exc:
            return f"error: {str(exc)[:100]}"

    db_status = await asyncio.get_event_loop().run_in_executor(None, _ping)
    return {"status": "running", "database": db_status}
