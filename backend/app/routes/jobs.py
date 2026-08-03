from datetime import datetime, timedelta, timezone
import os

from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from app.extensions import db
from app.models import Job

bp = Blueprint("jobs", __name__)

CATEGORIES = {"tech", "design", "marketing", "writing", "support", "finance"}
EXPERIENCE = {"internship", "entry", "mid", "senior"}
JOB_TYPES = {"full-time", "part-time", "contract", "freelance"}


def _parse_date_filter(value: str | None):
    if not value:
        return None
    now = datetime.now(timezone.utc)
    mapping = {
        "today": now - timedelta(days=1),
        "week": now - timedelta(days=7),
        "month": now - timedelta(days=30),
    }
    return mapping.get(value.lower())


def _pipeline_preferred() -> bool:
    """Serve Supabase/pickle pipeline when configured (Canada order)."""
    if os.getenv("USE_PIPELINE_STORE", "1") != "1":
        return False
    has_supabase = bool(
        os.getenv("SUPABASE_URL", "").strip()
        and (
            os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
            or os.getenv("SUPABASE_SERVICE_KEY", "").strip()
        )
    )
    cache = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "jobs_cache.pkl",
    )
    return has_supabase or os.path.exists(cache)


@bp.get("")
def list_jobs():
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(request.args.get("per_page", 20, type=int), 50)
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip().lower()
    experience = request.args.get("experience", "").strip().lower()
    job_type = request.args.get("job_type", "").strip().lower()
    salary_min = request.args.get("salary_min", type=int)
    date_posted = request.args.get("date_posted", "").strip().lower()
    featured_first = request.args.get("featured_first", "1") == "1"

    # Canada playbook: Supabase first, then pickle cache
    if _pipeline_preferred() and not any([category, experience, job_type, salary_min, date_posted]):
        try:
            from data_store import list_jobs_for_api

            payload = list_jobs_for_api(page=page, per_page=per_page, q=q)
            if payload.get("items") or payload.get("total"):
                return jsonify(payload)
        except Exception:
            pass

    query = Job.query.filter(Job.is_remote.is_(True))
    if hasattr(Job, "is_active"):
        query = query.filter(or_(Job.is_active.is_(True), Job.is_active.is_(None)))

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Job.title.ilike(like),
                Job.company.ilike(like),
                Job.description.ilike(like),
            )
        )
    if category and category in CATEGORIES:
        query = query.filter(Job.category == category)
    if experience and experience in EXPERIENCE:
        query = query.filter(Job.experience_level == experience)
    if job_type and job_type in JOB_TYPES:
        query = query.filter(Job.job_type == job_type)
    if salary_min is not None:
        query = query.filter(
            or_(Job.salary_min >= salary_min, Job.salary_max >= salary_min)
        )
    since = _parse_date_filter(date_posted)
    if since:
        query = query.filter(Job.posted_at >= since)

    if featured_first:
        query = query.order_by(Job.is_featured.desc(), Job.posted_at.desc())
    else:
        query = query.order_by(Job.posted_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "items": [job.to_dict() for job in pagination.items],
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "source": "sqlalchemy",
        }
    )


@bp.get("/<int:job_id>")
def get_job(job_id: int):
    job = Job.query.get_or_404(job_id)
    return jsonify(job.to_dict(include_description=True))


@bp.get("/meta/filters")
def filter_meta():
    return jsonify(
        {
            "categories": sorted(CATEGORIES),
            "experience_levels": sorted(EXPERIENCE),
            "job_types": sorted(JOB_TYPES),
            "date_posted": ["today", "week", "month"],
        }
    )


@bp.post("/scrape")
def trigger_scrape():
    """Manual scrape trigger for development / cron webhook.

    Default runs the JobSpy PK pipeline (scrape → pickle → upsert).
    Pass {"legacy": true} to only run Remotive/WWR SQLAlchemy upserts.
    """
    body = request.get_json(silent=True) or {}
    if body.get("legacy"):
        from app.scrapers.runner import run_all_scrapers

        result = run_all_scrapers()
        return jsonify({"ok": True, "mode": "legacy", **result})

    try:
        from data_store import dataframe_to_job_records, record_scrape_run, save_jobs_cache, upsert_jobs
        from scraper import scrape_all

        df = scrape_all(" ")
        save_jobs_cache(df)
        records = dataframe_to_job_records(df)
        result = upsert_jobs(records)
        record_scrape_run("completed", jobs_seen=len(records), message=str(result))
        return jsonify(
            {
                "ok": True,
                "mode": "pipeline",
                "jobs_seen": len(records),
                **result,
            }
        )
    except Exception as exc:
        try:
            from data_store import record_scrape_run

            record_scrape_run("failed", jobs_seen=0, message=str(exc))
        except Exception:
            pass
        return jsonify({"ok": False, "error": str(exc)}), 500
