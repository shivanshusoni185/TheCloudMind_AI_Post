import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .database import engine, Base, db_ping
from .routers import admin, news, contact
from .scheduler import start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)

try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified")
except Exception as exc:
    logger.error("Failed to create database tables: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="AI News API", version="1.0.0", lifespan=lifespan)

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

app.include_router(admin.router)
app.include_router(news.router)
app.include_router(contact.router)


@app.get("/")
async def root():
    return {"message": "AI News API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """
    Lightweight health probe for Fly.io.

    Uses db_ping() which opens its own connection outside the shared
    session pool — pool exhaustion during request bursts won't cause
    the health check to fail and trigger unnecessary machine restarts.
    """
    import asyncio
    ok = await asyncio.get_event_loop().run_in_executor(None, db_ping)
    return {"status": "running", "database": "connected" if ok else "unreachable"}
