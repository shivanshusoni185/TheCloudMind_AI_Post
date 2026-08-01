"""
Unit tests for the pure logic added with the jobs feature and URL changes.

Run inside the backend container:
    docker compose exec -T backend python -m pytest tests/ -q
(DATABASE_URL must be set — models import the DB engine at import time.)
"""

from datetime import datetime, timezone

from app.models import generate_slug
from app.services.jobs_fetcher import _map_job, _prettify_job_type, _parse_dt


# ── Slug generation ───────────────────────────────────────────────

def test_slug_basic():
    assert generate_slug("Hello World") == "hello-world"


def test_slug_strips_apostrophes():
    # Possessives must collapse, not create a stray "-s-".
    assert generate_slug("Australia's Role in the Race") == "australias-role-in-the-race"
    assert generate_slug("India's Win") == "indias-win"


def test_slug_special_chars_and_collapse():
    assert generate_slug("OpenAI Curbs GPT-5.6 Release!") == "openai-curbs-gpt-5-6-release"
    assert generate_slug("  multiple   spaces  ") == "multiple-spaces"


def test_slug_empty():
    assert generate_slug("") == ""


def test_slug_length_capped():
    assert len(generate_slug("word " * 200)) <= 250


# ── Jobs fetcher mapping ──────────────────────────────────────────

def _raw(**over):
    base = {
        "id": 123,
        "url": "https://remotive.com/job/123",
        "title": "Senior Engineer",
        "company_name": "Acme",
        "company_logo": "https://logo/acme.png",
        "category": "Software Development",
        "tags": ["Python", "AWS"],
        "job_type": "full_time",
        "publication_date": "2026-01-15T12:00:00",
        "candidate_required_location": "Worldwide",
        "salary": "$100k",
        "description": "<p>Great role</p>",
    }
    base.update(over)
    return base


def test_map_job_happy_path():
    m = _map_job(_raw())
    assert m["source_id"] == "123"
    assert m["title"] == "Senior Engineer"
    assert m["company"] == "Acme"
    assert m["remote"] is True
    assert m["job_type"] == "Full Time"        # prettified
    assert m["category"] == "Software Development"
    assert m["tags"] == ["Python", "AWS"]
    assert m["apply_url"] == "https://remotive.com/job/123"
    assert isinstance(m["posted_at"], datetime)


def test_map_job_missing_required_returns_none():
    assert _map_job(_raw(title=None)) is None
    assert _map_job(_raw(company_name="")) is None
    assert _map_job(_raw(url="")) is None


def test_map_job_defaults_location():
    m = _map_job(_raw(candidate_required_location=None))
    assert m["location"] == "Remote"


def test_map_job_tags_capped_and_clean():
    m = _map_job(_raw(tags=[f"t{i}" for i in range(20)] + ["", "  "]))
    assert len(m["tags"]) == 10
    assert "" not in m["tags"]


def test_prettify_job_type():
    assert _prettify_job_type("full_time") == "Full Time"
    assert _prettify_job_type(None) is None


def test_parse_dt_variants():
    assert _parse_dt("2026-01-15T12:00:00").tzinfo is not None
    assert _parse_dt(None) is None
    assert _parse_dt("not-a-date") is None
