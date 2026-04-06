import asyncio
import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from agents.auto_publish import run_auto_publish
from agents.agent_pipeline import run_agent_pipeline
from . import cache as news_cache

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None

# Grace period: if the job misfires (server busy / restarting at scheduled
# time), APScheduler will still run it within this window (seconds).
_MISFIRE_GRACE_SECS = 3600  # 1 hour


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# ── Blocking worker functions (run in thread pool, never block event loop) ──

def _auto_publish_worker() -> None:
    """Runs RSS auto-publish in a thread pool thread."""
    try:
        logger.info("[Scheduler] auto-publish job started")
        stats = run_auto_publish(
            max_per_topic=int(os.getenv("AUTO_PUBLISH_MAX_PER_TOPIC", "5"))
        )
        news_cache.invalidate()
        logger.info("[Scheduler] auto-publish completed: %s", stats)
    except Exception:
        logger.exception("[Scheduler] auto-publish job raised an unhandled exception")


def _agent_pipeline_worker() -> None:
    """Runs CrewAI agent pipeline in a thread pool thread."""
    try:
        logger.info("[Scheduler] agent pipeline job started")
        stats = run_agent_pipeline(
            max_per_topic=int(os.getenv("AGENT_PUBLISH_MAX_PER_TOPIC", "3"))
        )
        news_cache.invalidate()
        logger.info("[Scheduler] agent pipeline completed: %s", stats)
    except Exception:
        logger.exception("[Scheduler] agent pipeline job raised an unhandled exception")


# ── Async wrappers scheduled by APScheduler ────────────────────────────────

async def _run_auto_publish_job() -> None:
    """Offload blocking work to a thread so the event loop stays free."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _auto_publish_worker)


async def _run_agent_pipeline_job() -> None:
    """Offload blocking work to a thread so the event loop stays free."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _agent_pipeline_worker)


# ── Scheduler lifecycle ────────────────────────────────────────────────────

def start_scheduler() -> None:
    global _scheduler

    if _scheduler is not None:
        return

    if not _env_bool("AUTO_PUBLISH_ENABLED", True):
        logger.info("[Scheduler] disabled via AUTO_PUBLISH_ENABLED")
        return

    timezone = os.getenv("AUTO_PUBLISH_TIMEZONE", "Asia/Kolkata")
    hour = int(os.getenv("AUTO_PUBLISH_HOUR", "9"))
    minute = int(os.getenv("AUTO_PUBLISH_MINUTE", "0"))

    scheduler = AsyncIOScheduler(timezone=timezone)

    # RSS auto-publish at 09:00 IST daily
    scheduler.add_job(
        _run_auto_publish_job,
        CronTrigger(hour=hour, minute=minute, timezone=timezone),
        id="daily-auto-publish",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=_MISFIRE_GRACE_SECS,
    )

    # Agent pipeline runs 30 minutes after the RSS job (09:30 IST)
    agent_minute = (minute + 30) % 60
    agent_hour = (hour + (minute + 30) // 60) % 24
    scheduler.add_job(
        _run_agent_pipeline_job,
        CronTrigger(hour=agent_hour, minute=agent_minute, timezone=timezone),
        id="daily-agent-pipeline",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=_MISFIRE_GRACE_SECS,
    )

    scheduler.start()
    _scheduler = scheduler
    logger.info(
        "[Scheduler] started — auto-publish at %02d:%02d %s, "
        "agent pipeline at %02d:%02d %s",
        hour, minute, timezone,
        agent_hour, agent_minute, timezone,
    )

    if _env_bool("AUTO_PUBLISH_RUN_ON_STARTUP", False):
        logger.info("[Scheduler] AUTO_PUBLISH_RUN_ON_STARTUP=true — queuing immediate run")
        asyncio.ensure_future(_run_auto_publish_job())


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
