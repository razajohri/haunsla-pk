"""Additional remote job boards (worldwide-friendly public APIs).

Sources:
- RemoteOK
- Jobicy
- Arbeitnow
- Himalayas
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests

logger = logging.getLogger(__name__)
USER_AGENT = "HaunslaBot/1.0 (+https://haunsla.pk)"


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    return s


def _now() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _row(
    *,
    site: str,
    title: str,
    company: str,
    job_url: str,
    location: str = "Worldwide",
    description: str = "",
    date_posted: str | None = None,
    job_type: str | None = None,
    company_logo: str | None = None,
    salary_min: float | None = None,
    salary_max: float | None = None,
    currency: str = "USD",
) -> dict[str, Any]:
    return {
        "id": None,
        "site": site,
        "job_url": job_url,
        "job_url_direct": job_url,
        "title": title or "Untitled",
        "company": company or "Unknown",
        "location": location or "Worldwide",
        "date_posted": date_posted or _now(),
        "job_type": job_type,
        "salary_source": None,
        "interval": None,
        "min_amount": salary_min,
        "max_amount": salary_max,
        "currency": currency,
        "is_remote": True,
        "emails": None,
        "description": description or "",
        "company_url": None,
        "logo_photo_url": company_logo,
    }


def scrape_remoteok() -> pd.DataFrame:
    try:
        resp = _session().get("https://remoteok.com/api", timeout=40)
        resp.raise_for_status()
        payload = resp.json()
    except Exception:
        logger.exception("RemoteOK scrape failed")
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        # First payload row is legal/meta; real jobs have numeric ids + company + tags.
        if not item.get("id") or not item.get("company") or not item.get("position"):
            continue
        if not item.get("epoch") or not isinstance(item.get("tags"), list) or not item.get("tags"):
            continue
        apply_url = item.get("apply_url") or item.get("url") or ""
        if apply_url and apply_url.startswith("/"):
            apply_url = f"https://remoteok.com{apply_url}"
        if not apply_url or not str(apply_url).startswith("http"):
            continue
        title = str(item.get("position") or "")
        if len(title) < 3 or title.lower() in {"menu", "compatibility"}:
            continue
        loc = item.get("location") or "Worldwide"
        rows.append(
            _row(
                site="remoteok",
                title=title,
                company=item.get("company") or "",
                job_url=apply_url,
                location=str(loc),
                description=item.get("description") or "",
                date_posted=(str(item.get("date") or "")[:10] or None),
                company_logo=item.get("company_logo"),
                salary_min=item.get("salary_min"),
                salary_max=item.get("salary_max"),
            )
        )
    logger.info("RemoteOK: %s jobs", len(rows))
    return pd.DataFrame(rows)


def scrape_jobicy(count: int = 100) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    try:
        resp = _session().get(
            "https://jobicy.com/api/v2/remote-jobs",
            params={"count": count},
            timeout=40,
        )
        resp.raise_for_status()
        jobs = (resp.json() or {}).get("jobs") or []
    except Exception:
        logger.exception("Jobicy scrape failed")
        return pd.DataFrame()

    for item in jobs:
        url = item.get("url") or item.get("applicationLink") or ""
        if not url:
            continue
        loc = item.get("jobGeo") or item.get("jobLocation") or "Worldwide"
        rows.append(
            _row(
                site="jobicy",
                title=item.get("jobTitle") or "",
                company=item.get("companyName") or "",
                job_url=url,
                location=str(loc),
                description=item.get("jobDescription") or "",
                date_posted=(str(item.get("pubDate") or "")[:10] or None),
                job_type=item.get("jobType")[0] if isinstance(item.get("jobType"), list) and item.get("jobType") else item.get("jobType"),
                company_logo=item.get("companyLogo"),
                salary_min=item.get("annualSalaryMin"),
                salary_max=item.get("annualSalaryMax"),
                currency=item.get("salaryCurrency") or "USD",
            )
        )
    logger.info("Jobicy: %s jobs", len(rows))
    return pd.DataFrame(rows)


def scrape_arbeitnow() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    try:
        resp = _session().get("https://www.arbeitnow.com/api/job-board-api", timeout=40)
        resp.raise_for_status()
        jobs = (resp.json() or {}).get("data") or []
    except Exception:
        logger.exception("Arbeitnow scrape failed")
        return pd.DataFrame()

    for item in jobs:
        url = item.get("url") or ""
        if not url:
            continue
        remote = bool(item.get("remote"))
        if not remote:
            continue
        loc = item.get("location") or "Remote"
        rows.append(
            _row(
                site="arbeitnow",
                title=item.get("title") or "",
                company=item.get("company_name") or "",
                job_url=url,
                location=str(loc) if loc else "Remote",
                description=item.get("description") or "",
                date_posted=(str(item.get("created_at") or "")[:10] or None),
                job_type=",".join(item.get("job_types") or []) or None,
            )
        )
    logger.info("Arbeitnow: %s remote jobs", len(rows))
    return pd.DataFrame(rows)


def scrape_himalayas(limit: int = 100) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    offset = 0
    session = _session()
    while offset < limit:
        try:
            resp = session.get(
                "https://himalayas.app/jobs/api",
                params={"limit": min(20, limit - offset), "offset": offset},
                timeout=40,
            )
            resp.raise_for_status()
            payload = resp.json() or {}
            jobs = payload.get("jobs") or []
        except Exception:
            logger.exception("Himalayas scrape failed offset=%s", offset)
            break
        if not jobs:
            break
        for item in jobs:
            url = item.get("applicationLink") or item.get("guid") or item.get("url") or ""
            if not url:
                continue
            loc = item.get("location") or item.get("locationRestrictions") or "Worldwide"
            if isinstance(loc, list):
                loc = ", ".join(str(x) for x in loc) or "Worldwide"
            rows.append(
                _row(
                    site="himalayas",
                    title=item.get("title") or "",
                    company=item.get("companyName") or item.get("company") or "",
                    job_url=url,
                    location=str(loc),
                    description=item.get("description") or "",
                    date_posted=(str(item.get("pubDate") or item.get("updatedAt") or "")[:10] or None),
                    company_logo=item.get("companyLogo"),
                    salary_min=item.get("minSalary"),
                    salary_max=item.get("maxSalary"),
                    currency=item.get("currency") or "USD",
                )
            )
        offset += len(jobs)
        if offset >= int(payload.get("totalCount") or offset):
            break
    logger.info("Himalayas: %s jobs", len(rows))
    return pd.DataFrame(rows)


def scrape_remote_boards() -> pd.DataFrame:
    frames = [
        scrape_remoteok(),
        scrape_jobicy(),
        scrape_arbeitnow(),
        scrape_himalayas(),
    ]
    nonempty = [f for f in frames if f is not None and not f.empty]
    if not nonempty:
        return pd.DataFrame()
    return pd.concat(nonempty, ignore_index=True)
