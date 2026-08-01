import asyncio
import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from agents.auto_publish import run_auto_publish
from agents.agent_pipeline import run_agent_pipeline
from . import cache as news_cache

try:
    import fcntl  # POSIX only; present in the Linux container
except ImportError:  # e.g. local Windows dev — single process, no lock needed
    fcntl = None

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None

# Held open for the process lifetime to keep the cross-worker lock. Without a
# module-level reference the file object would be GC'd and the lock released.
_lock_file = None


def _acquire_scheduler_lock() -> bool:
    """Return True if this process should run the scheduler.

    With ``uvicorn --workers N`` every worker is a separate process and each
    calls ``start_scheduler()``. An exclusive non-blocking ``flock`` lets only
    the first worker win, so the daily jobs fire exactly once. The lock is tied
    to the file descriptor and auto-released by the OS if that worker exits, so
    a respawned worker can take over on its next startup.
    """
    global _lock_file
    if fcntl is None:  # no flock available — assume single process
        return True
    path = os.getenv("SCHEDULER_LOCK_PATH", "/tmp/cloudmind-scheduler.lock")
    try:
        f = open(path, "w")
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    _lock_file = f
    return True

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

    # Only one worker process may own the scheduler (see _acquire_scheduler_lock).
    if not _acquire_scheduler_lock():
        logger.info("[Scheduler] another worker holds the lock — not starting in this worker")
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
