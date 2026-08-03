"""Ashby / Greenhouse / Lever board scrapers (JobSpy-compatible rows).

Public python-jobspy does not ship these ATS boards; the Canada app used a
vendored JobSpy fork. Haunsla hits the public board APIs directly and returns
a pandas DataFrame with the same column shape JobSpy uses.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests

from ats_companies import get_ats_company_lists, patch_jobspy_company_lists
from ats_location import is_pakistan_job_row

logger = logging.getLogger(__name__)

USER_AGENT = "HaunslaBot/1.0 (+https://haunsla.pk)"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
ATS_REQUEST_DELAY_SEC = float(__import__("os").getenv("ATS_REQUEST_DELAY_SEC", "0.15"))


def _now_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _row(
    *,
    site: str,
    title: str,
    company: str,
    job_url: str,
    job_url_direct: str | None = None,
    location: str = "",
    description: str = "",
    job_type: str | None = None,
    date_posted: str | None = None,
    is_remote: bool = True,
    company_url: str | None = None,
) -> dict[str, Any]:
    return {
        "id": None,
        "site": site,
        "job_url": job_url,
        "job_url_direct": job_url_direct or job_url,
        "title": title,
        "company": company,
        "location": location or "",
        "date_posted": date_posted or _now_date(),
        "job_type": job_type,
        "salary_source": None,
        "interval": None,
        "min_amount": None,
        "max_amount": None,
        "currency": "USD",
        "is_remote": is_remote,
        "emails": None,
        "description": description or "",
        "company_url": company_url,
        "logo_photo_url": None,
    }


def _fetch_greenhouse(slug: str) -> list[dict[str, Any]]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        resp = SESSION.get(url, params={"content": "true"}, timeout=30)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        payload = resp.json()
    except Exception:
        logger.exception("Greenhouse fetch failed for %s", slug)
        return []

    company = slug.replace("-", " ").title()
    rows: list[dict[str, Any]] = []
    for job in payload.get("jobs") or []:
        loc = ""
        if isinstance(job.get("location"), dict):
            loc = job["location"].get("name") or ""
        elif job.get("location"):
            loc = str(job.get("location"))
        offices = job.get("offices") or []
        if not loc and offices:
            loc = ", ".join(
                o.get("name") for o in offices if isinstance(o, dict) and o.get("name")
            )
        blob = f"{loc} {job.get('title') or ''} {job.get('content') or ''}".lower()
        remote = "remote" in blob or "work from home" in blob or "distributed" in blob
        rows.append(
            _row(
                site="greenhouse",
                title=job.get("title") or "Untitled",
                company=company,
                job_url=job.get("absolute_url") or "",
                location=loc,
                description=job.get("content") or "",
                is_remote=remote,
                company_url=f"https://boards.greenhouse.io/{slug}",
            )
        )
    return rows


def _fetch_lever(slug: str) -> list[dict[str, Any]]:
    url = f"https://api.lever.co/v0/postings/{slug}"
    try:
        resp = SESSION.get(url, params={"mode": "json"}, timeout=30)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        payload = resp.json()
    except Exception:
        logger.exception("Lever fetch failed for %s", slug)
        return []

    if not isinstance(payload, list):
        return []

    company = slug.replace("-", " ").title()
    rows: list[dict[str, Any]] = []
    for job in payload:
        cats = job.get("categories") or {}
        loc = cats.get("location") or ""
        commitment = cats.get("commitment")
        text_blob = f"{loc} {job.get('text') or ''} {job.get('descriptionPlain') or ''}"
        remote = "remote" in text_blob.lower()
        created = job.get("createdAt")
        date_posted = None
        if isinstance(created, (int, float)):
            date_posted = datetime.fromtimestamp(created / 1000, tz=timezone.utc).date().isoformat()
        rows.append(
            _row(
                site="lever",
                title=job.get("text") or "Untitled",
                company=company,
                job_url=job.get("hostedUrl") or job.get("applyUrl") or "",
                job_url_direct=job.get("applyUrl") or job.get("hostedUrl") or "",
                location=loc,
                description=job.get("descriptionPlain") or job.get("description") or "",
                job_type=commitment,
                date_posted=date_posted,
                is_remote=remote,
                company_url=f"https://jobs.lever.co/{slug}",
            )
        )
    return rows


def _fetch_ashby(slug: str) -> list[dict[str, Any]]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    try:
        resp = SESSION.get(url, timeout=30)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        payload = resp.json()
    except Exception:
        logger.exception("Ashby fetch failed for %s", slug)
        return []

    company = slug.replace("-", " ").title()
    rows: list[dict[str, Any]] = []
    for job in payload.get("jobs") or []:
        loc_parts = []
        if job.get("location"):
            loc_parts.append(str(job["location"]))
        for loc in job.get("locations") or []:
            if isinstance(loc, dict) and loc.get("name"):
                loc_parts.append(str(loc["name"]))
            elif isinstance(loc, str):
                loc_parts.append(loc)
        loc = ", ".join(dict.fromkeys(loc_parts))
        remote = bool(job.get("isRemote")) or "remote" in loc.lower()
        rows.append(
            _row(
                site="ashby",
                title=job.get("title") or "Untitled",
                company=company,
                job_url=job.get("jobUrl") or job.get("applyUrl") or "",
                job_url_direct=job.get("applyUrl") or job.get("jobUrl") or "",
                location=loc,
                description=job.get("descriptionPlain") or job.get("descriptionHtml") or "",
                job_type=(job.get("employmentType") or None),
                date_posted=(job.get("publishedAt") or _now_date())[:10],
                is_remote=remote,
                company_url=f"https://jobs.ashbyhq.com/{slug}",
            )
        )
    return rows


def scrape_ats(
    search_terms: tuple[str, ...] | list[str] | None = None,
    results_wanted: int = 2500,
) -> pd.DataFrame:
    """Fetch ATS boards and optionally keyword-filter titles/descriptions."""
    patch_jobspy_company_lists()
    lists = get_ats_company_lists()
    terms = [t.lower().strip() for t in (search_terms or ()) if t and t.strip()]

    rows: list[dict[str, Any]] = []
    for slug in lists["greenhouse"]:
        rows.extend(_fetch_greenhouse(slug))
    for slug in lists["lever"]:
        rows.extend(_fetch_lever(slug))
    for slug in lists["ashby"]:
        rows.extend(_fetch_ashby(slug))

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    # Prefer remote-looking rows; then apply PK/worldwide filter
    if "is_remote" in df.columns:
        # Keep rows that look remote OR pass location filter later
        pass

    if terms:
        def matches(row: pd.Series) -> bool:
            blob = f"{row.get('title') or ''} {row.get('description') or ''}".lower()
            return any(term in blob for term in terms)

        # Keep if any term matches OR term is generic "remote"
        if not (len(terms) == 1 and terms[0] == "remote"):
            non_remote = [t for t in terms if t != "remote"]
            if non_remote:
                df = df[df.apply(matches, axis=1)]

    df = df[df.apply(is_pakistan_job_row, axis=1)].reset_index(drop=True)
    if results_wanted and len(df) > results_wanted:
        df = df.head(results_wanted).reset_index(drop=True)
    return df
