from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from app.extensions import db
from app.models import Job

bp = Blueprint("jobs", __name__)

CATEGORIES = {"tech", "design", "marketing", "writing", "support", "finance"}
EXPERIENCE = {"entry", "mid", "senior"}
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

    query = Job.query.filter(Job.is_remote.is_(True))

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
    """Manual scrape trigger for development / cron webhook."""
    from app.scrapers.runner import run_all_scrapers

    result = run_all_scrapers()
    return jsonify({"ok": True, **result})
