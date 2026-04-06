import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from agents.auto_publish import run_auto_publish
from agents.agent_pipeline import run_agent_pipeline
from . import cache as news_cache

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _run_job() -> None:
    logger.info("Starting scheduled auto-publish job (RSS feeds)")
    stats = run_auto_publish(max_per_topic=int(os.getenv("AUTO_PUBLISH_MAX_PER_TOPIC", "5")))
    news_cache.invalidate()
    logger.info("Scheduled auto-publish completed: %s", stats)


def _run_agent_job() -> None:
    logger.info("Starting scheduled agent pipeline job (DuckDuckGo)")
    stats = run_agent_pipeline(max_per_topic=int(os.getenv("AGENT_PUBLISH_MAX_PER_TOPIC", "3")))
    news_cache.invalidate()
    logger.info("Scheduled agent pipeline completed: %s", stats)


def start_scheduler() -> None:
    global _scheduler

    if _scheduler is not None:
        return

    if not _env_bool("AUTO_PUBLISH_ENABLED", True):
        logger.info("Auto-publish scheduler is disabled")
        return

    timezone = os.getenv("AUTO_PUBLISH_TIMEZONE", "Asia/Kolkata")
    hour = int(os.getenv("AUTO_PUBLISH_HOUR", "9"))
    minute = int(os.getenv("AUTO_PUBLISH_MINUTE", "0"))

    scheduler = AsyncIOScheduler(timezone=timezone)
    scheduler.add_job(
        _run_job,
        CronTrigger(hour=hour, minute=minute, timezone=timezone),
        id="daily-auto-publish",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # Agent pipeline runs 30 minutes after the RSS job
    agent_hour = int(os.getenv("AGENT_PUBLISH_HOUR", str(hour)))
    agent_minute = (minute + 30) % 60
    agent_hour_adj = (agent_hour + (minute + 30) // 60) % 24
    scheduler.add_job(
        _run_agent_job,
        CronTrigger(hour=agent_hour_adj, minute=agent_minute, timezone=timezone),
        id="daily-agent-pipeline",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()
    _scheduler = scheduler
    logger.info(
        "Auto-publish scheduler started for %02d:%02d %s",
        hour,
        minute,
        timezone,
    )

    if _env_bool("AUTO_PUBLISH_RUN_ON_STARTUP", False):
        logger.info("AUTO_PUBLISH_RUN_ON_STARTUP enabled; running immediately")
        _run_job()


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
