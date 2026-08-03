"""Job cache + Supabase upsert + serve helpers (Canada playbook shape)."""

from __future__ import annotations

import hashlib
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from ats_location import is_pakistan_job_row

logger = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parent
CACHE_PATH = Path(os.getenv("JOBS_CACHE_PATH", str(BACKEND_ROOT / "jobs_cache.pkl")))
JOB_CACHE_TTL_SECONDS = int(os.getenv("JOB_CACHE_TTL_SECONDS", "900"))
UPSERT_CHUNK_SIZE = int(os.getenv("UPSERT_CHUNK_SIZE", "500"))

LISTED_JOB_SITES = {
    "ashby",
    "greenhouse",
    "lever",
    "hiringcafe",
    "indeed",
    "linkedin",
    "remotive",
    "weworkremotely",
    "remoteok",
    "jobicy",
    "arbeitnow",
    "himalayas",
    "bayt",
    "naukri",
    "repstack",
}


def _supabase_client():
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_KEY", "").strip()
    )
    if not url or not key:
        return None
    try:
        from supabase import create_client

        return create_client(url, key)
    except Exception:
        logger.exception("Failed to create Supabase client")
        return None


def _build_source_key(
    site: str,
    job_url: str,
    title: str,
    company: str,
) -> str:
    raw = f"{site}|{job_url}|{title}|{company}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _clean_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return default
    return text


def build_job_record(row: dict[str, Any] | pd.Series) -> dict[str, Any] | None:
    site = _clean_str(row.get("site"), "unknown").lower()
    job_url_direct = _clean_str(row.get("job_url_direct")) or None
    job_url = _clean_str(row.get("job_url")) or job_url_direct
    if not job_url:
        return None
    title = _clean_str(row.get("title"), "Untitled") or "Untitled"
    company = _clean_str(row.get("company"), "Unknown") or "Unknown"
    url_for_key = str(job_url_direct or job_url)
    source_key = _build_source_key(site, url_for_key, title, company)

    min_amount = row.get("min_amount")
    max_amount = row.get("max_amount")
    try:
        min_amount = float(min_amount) if min_amount is not None and str(min_amount) not in ("", "nan") else None
    except (TypeError, ValueError):
        min_amount = None
    try:
        max_amount = float(max_amount) if max_amount is not None and str(max_amount) not in ("", "nan") else None
    except (TypeError, ValueError):
        max_amount = None

    date_posted = row.get("date_posted")
    if hasattr(date_posted, "isoformat"):
        date_posted = date_posted.isoformat()
    elif date_posted is not None:
        date_posted = str(date_posted)[:32] or None

    currency = row.get("currency") or "USD"
    if isinstance(currency, str) and currency.upper() == "CAD":
        currency = "USD"

    raw_payload = row.to_dict() if hasattr(row, "to_dict") else dict(row)
    # Make JSON-safe
    for key, value in list(raw_payload.items()):
        if hasattr(value, "isoformat"):
            raw_payload[key] = value.isoformat()
        elif pd.isna(value) if not isinstance(value, (list, dict)) else False:
            raw_payload[key] = None
        elif hasattr(value, "item"):
            try:
                raw_payload[key] = value.item()
            except Exception:
                raw_payload[key] = str(value)

    compensation = row.get("compensation")
    if compensation is None and (min_amount or max_amount):
        lo = int(min_amount) if min_amount is not None else ""
        hi = int(max_amount) if max_amount is not None else ""
        if lo or hi:
            compensation = f"{currency} {lo}-{hi}".strip()

    experience_level = row.get("experience_level")
    if isinstance(experience_level, str):
        experience_level = experience_level.strip().lower() or None
    else:
        experience_level = None

    tags = row.get("tags")
    if not isinstance(tags, list):
        tags = ["Remote"]
    if experience_level == "internship" and "Internship" not in tags:
        tags = [*tags, "Internship"]
    if experience_level == "entry" and "Entry Level" not in tags:
        tags = [*tags, "Entry Level"]

    return {
        "source_key": source_key,
        "site": site,
        "title": title,
        "company": company,
        "location": str(row.get("location") or "") or None,
        "description": str(row.get("description") or ""),
        "compensation": compensation,
        "interval": row.get("interval"),
        "min_amount": min_amount,
        "max_amount": max_amount,
        "currency": currency,
        "job_type": row.get("job_type"),
        "experience_level": experience_level,
        "tags": tags,
        "job_url": str(job_url),
        "job_url_direct": str(job_url_direct) if job_url_direct else None,
        "date_posted": date_posted,
        "is_remote": bool(row.get("is_remote", True)),
        "is_active": True,
        "raw_payload": raw_payload,
    }


def dataframe_to_job_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        rec = build_job_record(row)
        if rec:
            records.append(rec)
    return records


def save_jobs_cache(df: pd.DataFrame, path: Path | None = None) -> Path:
    target = path or CACHE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix="jobs_cache_", suffix=".pkl", dir=str(target.parent))
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        df.to_pickle(tmp_path)
        os.replace(tmp_path, target)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
    logger.info("Wrote jobs cache %s (%s rows)", target, len(df))
    return target


def load_jobs_cache(path: Path | None = None) -> pd.DataFrame:
    target = path or CACHE_PATH
    if not target.exists():
        return pd.DataFrame()
    try:
        df = pd.read_pickle(target)
        if not isinstance(df, pd.DataFrame):
            return pd.DataFrame()
        return df
    except Exception:
        logger.exception("Failed to load jobs cache %s", target)
        return pd.DataFrame()


def record_scrape_run(
    status: str,
    jobs_seen: int = 0,
    message: str | None = None,
) -> None:
    client = _supabase_client()
    if client is None:
        logger.info("scrape_run status=%s jobs_seen=%s message=%s", status, jobs_seen, message)
        return
    try:
        client.table("scrape_runs").insert(
            {
                "status": status,
                "jobs_seen": jobs_seen,
                "message": message,
            }
        ).execute()
    except Exception:
        logger.exception("Failed to record scrape_run")


def upsert_jobs(records: list[dict[str, Any]]) -> dict[str, int]:
    if not records:
        return {"upserted": 0, "chunks": 0}

    client = _supabase_client()
    if client is not None:
        return _upsert_supabase(client, records)

    return _upsert_sqlalchemy(records)


def _upsert_supabase(client, records: list[dict[str, Any]]) -> dict[str, int]:
    chunks = 0
    upserted = 0
    for i in range(0, len(records), UPSERT_CHUNK_SIZE):
        chunk = records[i : i + UPSERT_CHUNK_SIZE]
        client.table("jobs").upsert(chunk, on_conflict="source_key").execute()
        chunks += 1
        upserted += len(chunk)
    logger.info("Supabase upserted %s jobs in %s chunks", upserted, chunks)
    return {"upserted": upserted, "chunks": chunks}


def _map_record_to_orm_fields(rec: dict[str, Any]) -> dict[str, Any]:
    apply_url = rec.get("job_url_direct") or rec.get("job_url") or ""
    job_type = rec.get("job_type")
    if isinstance(job_type, str):
        jt = job_type.lower().replace(" ", "-").replace("_", "-")
        if jt in {"full-time", "fulltime"}:
            jt = "full-time"
        elif jt in {"part-time", "parttime"}:
            jt = "part-time"
        elif "contract" in jt:
            jt = "contract"
        elif "freelance" in jt:
            jt = "freelance"
        else:
            jt = jt[:32]
    else:
        jt = "full-time"

    posted_at = rec.get("date_posted")
    if isinstance(posted_at, str) and posted_at:
        try:
            posted_at = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
        except ValueError:
            posted_at = datetime.now(timezone.utc)
    elif posted_at is None:
        posted_at = datetime.now(timezone.utc)

    salary_min = int(rec["min_amount"]) if rec.get("min_amount") is not None else None
    salary_max = int(rec["max_amount"]) if rec.get("max_amount") is not None else None

    tags = ["Remote"]
    if rec.get("location"):
        tags.append(str(rec["location"])[:40])
    if rec.get("site"):
        tags.append(str(rec["site"]).title())

    exp = rec.get("experience_level")
    if isinstance(exp, str):
        exp = exp.strip().lower() or None
    else:
        exp = None
    if exp == "internship" and "Internship" not in tags:
        tags.append("Internship")
    if exp == "entry" and "Entry Level" not in tags:
        tags.append("Entry Level")

    return {
        "external_id": rec["source_key"],
        "source_key": rec["source_key"],
        "site": rec.get("site"),
        "title": rec["title"],
        "company": rec["company"],
        "location": rec.get("location"),
        "description": rec.get("description") or "",
        "apply_url": apply_url,
        "job_url": rec.get("job_url"),
        "job_url_direct": rec.get("job_url_direct"),
        "compensation": rec.get("compensation"),
        "pay_interval": rec.get("interval"),
        "job_type": jt,
        "experience_level": exp,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": rec.get("currency") or "USD",
        "tags": tags,
        "source": rec.get("site"),
        "is_remote": bool(rec.get("is_remote", True)),
        "pakistan_friendly": True,
        "is_active": bool(rec.get("is_active", True)),
        "raw_payload": rec.get("raw_payload") or {},
        "posted_at": posted_at,
        "company_logo": (rec.get("raw_payload") or {}).get("logo_photo_url"),
    }


def _upsert_sqlalchemy(records: list[dict[str, Any]]) -> dict[str, int]:
    from flask import has_app_context

    from app.extensions import db
    from app.models import Job

    def _write() -> int:
        count = 0
        for rec in records:
            fields = _map_record_to_orm_fields(rec)
            existing = Job.query.filter(
                (Job.source_key == fields["source_key"])
                | (Job.external_id == fields["external_id"])
            ).first()
            if existing:
                for key, value in fields.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
            else:
                db.session.add(Job(**{k: v for k, v in fields.items() if hasattr(Job, k)}))
            count += 1
            if count % UPSERT_CHUNK_SIZE == 0:
                db.session.commit()
        db.session.commit()
        return count

    if has_app_context():
        upserted = _write()
    else:
        from app import create_app

        app = create_app()
        with app.app_context():
            upserted = _write()

    logger.info("SQLAlchemy upserted %s jobs", upserted)
    return {"upserted": upserted, "chunks": max(1, upserted // UPSERT_CHUNK_SIZE)}


def _record_to_api_job(rec: dict[str, Any], *, include_description: bool = False) -> dict[str, Any]:
    """Map Canada-shaped record → Haunsla mobile Job JSON."""
    apply_url = rec.get("job_url_direct") or rec.get("apply_url") or rec.get("job_url")
    source_key = rec.get("source_key") or rec.get("external_id")
    # Stable numeric id for mobile when only source_key exists
    numeric_id = rec.get("id")
    if numeric_id is None and source_key:
        numeric_id = int(hashlib.sha256(source_key.encode()).hexdigest()[:12], 16) % (10**9)

    job_type = rec.get("job_type") or "full-time"
    if isinstance(job_type, str):
        job_type = job_type.lower().replace(" ", "-")

    data = {
        "id": numeric_id,
        "external_id": source_key,
        "title": rec.get("title"),
        "company": rec.get("company"),
        "company_logo": rec.get("company_logo")
        or (rec.get("raw_payload") or {}).get("logo_photo_url"),
        "apply_url": apply_url,
        "category": rec.get("category"),
        "experience_level": rec.get("experience_level")
        or (rec.get("raw_payload") or {}).get("experience_level"),
        "job_type": job_type,
        "salary_min": _as_int(rec.get("salary_min", rec.get("min_amount"))),
        "salary_max": _as_int(rec.get("salary_max", rec.get("max_amount"))),
        "salary_currency": rec.get("salary_currency") or rec.get("currency") or "USD",
        "tags": rec.get("tags") or ["Remote"],
        "source": rec.get("source") or rec.get("site"),
        "is_remote": bool(rec.get("is_remote", True)),
        "pakistan_friendly": bool(rec.get("pakistan_friendly", True)),
        "haunsla_score": rec.get("haunsla_score"),
        "is_featured": bool(rec.get("is_featured", False)),
        "posted_at": _iso(rec.get("posted_at") or rec.get("date_posted")),
        "created_at": _iso(rec.get("created_at")),
        "location": rec.get("location"),
    }
    if include_description:
        data["description"] = rec.get("description") or ""
    return data


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _serve_filter_row(row: dict[str, Any] | pd.Series) -> bool:
    site = str(row.get("site") or row.get("source") or "").lower()
    if site and site not in LISTED_JOB_SITES:
        return False
    if row.get("is_active") is False:
        return False
    return is_pakistan_job_row(row)


def list_jobs_from_supabase(
    *,
    page: int = 1,
    per_page: int = 20,
    q: str = "",
) -> dict[str, Any] | None:
    client = _supabase_client()
    if client is None:
        return None
    try:
        query = (
            client.table("jobs")
            .select("*", count="exact")
            .eq("is_active", True)
            .eq("is_remote", True)
            .in_("site", list(LISTED_JOB_SITES))
            .order("date_posted", desc=True)
        )
        if q:
            # PostgREST or-filter
            query = query.or_(f"title.ilike.%{q}%,company.ilike.%{q}%")
        start = (page - 1) * per_page
        end = start + per_page - 1
        result = query.range(start, end).execute()
        rows = result.data or []
        # Serve-time PK re-filter
        rows = [r for r in rows if _serve_filter_row(r)]
        total = result.count if result.count is not None else len(rows)
        items = [_record_to_api_job(r) for r in rows]
        pages = max(1, (total + per_page - 1) // per_page) if total else 1
        return {
            "items": items,
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
            "has_next": page < pages,
            "source": "supabase",
        }
    except Exception:
        logger.exception("Supabase list_jobs failed")
        return None


def list_jobs_from_cache(
    *,
    page: int = 1,
    per_page: int = 20,
    q: str = "",
) -> dict[str, Any]:
    df = load_jobs_cache()
    if df.empty:
        return {
            "items": [],
            "page": page,
            "per_page": per_page,
            "total": 0,
            "pages": 0,
            "has_next": False,
            "source": "cache",
        }

    if "site" in df.columns:
        df = df[df["site"].astype(str).str.lower().isin(LISTED_JOB_SITES)]
    df = df[df.apply(_serve_filter_row, axis=1)]
    if q:
        ql = q.lower()
        df = df[
            df.apply(
                lambda r: ql in str(r.get("title") or "").lower()
                or ql in str(r.get("company") or "").lower()
                or ql in str(r.get("description") or "").lower(),
                axis=1,
            )
        ]
    if "date_posted" in df.columns:
        df = df.sort_values("date_posted", ascending=False)
    total = len(df)
    start = (page - 1) * per_page
    end = start + per_page
    page_df = df.iloc[start:end]
    items = [_record_to_api_job(build_job_record(row) or {}) for _, row in page_df.iterrows()]
    pages = max(1, (total + per_page - 1) // per_page) if total else 0
    return {
        "items": items,
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "has_next": page < pages,
        "source": "cache",
    }


def list_jobs_for_api(
    *,
    page: int = 1,
    per_page: int = 20,
    q: str = "",
) -> dict[str, Any]:
    """Supabase first, then pickle cache (Canada serve order)."""
    remote = list_jobs_from_supabase(page=page, per_page=per_page, q=q)
    if remote is not None and (remote["items"] or remote["total"]):
        return remote
    return list_jobs_from_cache(page=page, per_page=per_page, q=q)
