"""
Fetch broad tech/all-role jobs from a free public jobs API and upsert them.

Uses Remotive (https://remotive.com/api/remote-jobs) — free, no API key,
broad categories (software-dev, data, design, marketing, sales, product,
finance, HR, QA, writing, …). Idempotent: each listing is deduped by
(source, source_id) so re-runs update rather than duplicate.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import requests
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Job, generate_slug

logger = logging.getLogger(__name__)

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"
SOURCE = "remotive"
_TIMEOUT = 20
_USER_AGENT = "TheCloudMind.ai jobs board (+https://cloudmindai.in)"


def _prettify_job_type(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return value.replace("_", " ").replace("-", " ").strip().title()


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        # Remotive returns e.g. "2024-01-15T12:00:00" (naive UTC)
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _clip(value: Optional[str], length: int) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value[:length] if value else None


def _map_job(raw: dict) -> Optional[dict]:
    title = _clip(raw.get("title"), 300)
    company = _clip(raw.get("company_name"), 255)
    apply_url = (raw.get("url") or "").strip()
    if not (title and company and apply_url):
        return None

    tags = raw.get("tags") if isinstance(raw.get("tags"), list) else []
    return {
        "source_id": str(raw.get("id")),
        "title": title,
        "company": company,
        "location": _clip(raw.get("candidate_required_location"), 255) or "Remote",
        "remote": True,  # Remotive is remote-only
        "job_type": _clip(_prettify_job_type(raw.get("job_type")), 100),
        "category": _clip(raw.get("category"), 100),
        "tags": [str(t).strip() for t in tags if str(t).strip()][:10],
        "description": raw.get("description") or None,
        "apply_url": apply_url[:1000],
        "company_logo": _clip(raw.get("company_logo"), 1000),
        "salary": _clip(raw.get("salary"), 255),
        "posted_at": _parse_dt(raw.get("publication_date")),
    }


def _unique_slug(db: Session, title: str, company: str) -> str:
    base = f"{title} at {company}" if company else title
    return generate_slug(base, db, Job)


def fetch_and_store_jobs(limit: int = 100) -> dict:
    """Fetch up to ``limit`` jobs from Remotive and upsert them. Returns stats."""
    stats = {"fetched": 0, "created": 0, "updated": 0, "failed": 0}
    try:
        resp = requests.get(
            REMOTIVE_URL,
            params={"limit": max(1, min(limit, 200))},
            headers={"User-Agent": _USER_AGENT, "Accept": "application/json"},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        logger.exception("[Jobs] fetch failed: %s", exc)
        return stats

    jobs = payload.get("jobs") or []
    stats["fetched"] = len(jobs)

    db = SessionLocal()
    try:
        for raw in jobs:
            mapped = _map_job(raw)
            if not mapped:
                stats["failed"] += 1
                continue
            try:
                existing = (
                    db.query(Job)
                    .filter(Job.source == SOURCE, Job.source_id == mapped["source_id"])
                    .first()
                )
                if existing:
                    for key, value in mapped.items():
                        if key == "source_id":
                            continue
                        setattr(existing, key, value)
                    stats["updated"] += 1
                else:
                    job = Job(source=SOURCE, published=True, pinned=False, **mapped)
                    job.slug = _unique_slug(db, mapped["title"], mapped["company"])
                    db.add(job)
                    stats["created"] += 1
                db.commit()
            except Exception as exc:
                db.rollback()
                stats["failed"] += 1
                logger.warning("[Jobs] failed to store '%s': %s", mapped.get("title"), exc)
    finally:
        db.close()

    logger.info("[Jobs] fetch complete: %s", stats)
    return stats
