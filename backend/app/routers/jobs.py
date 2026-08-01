from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, cast, Text
from sqlalchemy.orm import Session, load_only

from ..database import get_db
from ..models import Job
from ..schemas import JobResponse, JobListResponse
from .. import cache

router = APIRouter(prefix="/jobs", tags=["jobs"])

_LIST_COLS = [
    Job.id, Job.title, Job.company, Job.location, Job.remote,
    Job.job_type, Job.category, Job.tags, Job.company_logo, Job.salary,
    Job.pinned, Job.posted_at, Job.created_at, Job.slug,
]


@router.get("", response_model=list[JobListResponse])
def list_jobs(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    remote: Optional[bool] = Query(None),
    tag: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    cache_key = f"jobs_list:{search or ''}:{category or ''}:{remote}:{tag or ''}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    query = (
        db.query(Job)
        .options(load_only(*_LIST_COLS))
        .filter(Job.published == True)  # noqa: E712
    )

    if search:
        term = f"%{search}%"
        query = query.filter(or_(Job.title.ilike(term), Job.company.ilike(term)))
    if category:
        query = query.filter(Job.category.ilike(category))
    if remote is not None:
        query = query.filter(Job.remote == remote)
    if tag:
        query = query.filter(cast(Job.tags, Text).ilike(f"%{tag}%"))

    rows = (
        query.order_by(
            Job.pinned.desc(),
            Job.posted_at.desc().nullslast(),
            Job.created_at.desc(),
        )
        .limit(300)
        .all()
    )

    result = [JobListResponse.model_validate(item) for item in rows]
    cache.set(cache_key, result)
    return result


@router.get("/categories", response_model=list[str])
def list_categories(db: Session = Depends(get_db)):
    cached = cache.get("jobs_categories")
    if cached is not None:
        return cached
    rows = (
        db.query(Job.category)
        .filter(Job.published == True, Job.category.isnot(None))  # noqa: E712
        .distinct()
        .all()
    )
    result = sorted({r[0] for r in rows if r[0]})
    cache.set("jobs_categories", result)
    return result


@router.get("/by-slug/{slug}", response_model=JobResponse)
def get_job_by_slug(slug: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.slug == slug, Job.published == True).first()  # noqa: E712
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id, Job.published == True).first()  # noqa: E712
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
