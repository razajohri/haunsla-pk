"""Optional hiring.cafe SSR scrape (opt-in via SCRAPE_HIRING_CAFE=1)."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any
from urllib.parse import quote

import pandas as pd
import requests
from bs4 import BeautifulSoup

from ats_location import is_pakistan_job_row

logger = logging.getLogger(__name__)

USER_AGENT = "HaunslaBot/1.0 (+https://haunsla.pk)"
BASE = "https://hiring.cafe"


def _max_pages() -> int:
    return int(os.getenv("HIRING_CAFE_MAX_PAGES", "5"))


def _max_jobs() -> int:
    return int(os.getenv("HIRING_CAFE_MAX_JOBS", "200"))


def _search_url(page: int = 1) -> str:
    # Broad remote search; PK filter applied after parse
    query = quote("remote")
    return f"{BASE}/?search={query}&page={page}"


def _parse_next_data(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    script = soup.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        return []
    try:
        payload = json.loads(script.string)
    except json.JSONDecodeError:
        return []

    # Walk for job-like dicts
    found: list[dict[str, Any]] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if ("title" in node or "jobTitle" in node) and (
                "company" in node or "companyName" in node or "organization" in node
            ):
                found.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return found


def _map_hit(hit: dict[str, Any]) -> dict[str, Any] | None:
    title = hit.get("title") or hit.get("jobTitle")
    organization = hit.get("organization")
    if isinstance(organization, dict):
        organization_name = organization.get("name")
    else:
        organization_name = organization
    company = hit.get("company") or hit.get("companyName") or organization_name
    job_url = (
        hit.get("job_url")
        or hit.get("url")
        or hit.get("applyUrl")
        or hit.get("jobUrl")
        or hit.get("link")
    )
    if not title or not job_url:
        return None
    location = hit.get("location") or hit.get("locations") or "Remote"
    if isinstance(location, list):
        location = ", ".join(str(x) for x in location)
    return {
        "id": hit.get("id"),
        "site": "hiringcafe",
        "job_url": str(job_url),
        "job_url_direct": str(hit.get("applyUrl") or job_url),
        "title": str(title),
        "company": str(company or "Unknown"),
        "location": str(location),
        "date_posted": str(hit.get("date_posted") or hit.get("publishedAt") or "")[:10] or None,
        "job_type": hit.get("job_type") or hit.get("employmentType") or "Full Time",
        "interval": hit.get("interval") or "Yearly",
        "min_amount": hit.get("min_amount") or hit.get("salaryMin"),
        "max_amount": hit.get("max_amount") or hit.get("salaryMax"),
        "currency": hit.get("currency") or "USD",
        "is_remote": True,
        "description": hit.get("description") or hit.get("descriptionPlain") or "",
        "company_url": hit.get("company_url"),
        "skills": hit.get("skills"),
        "work_from_home_type": hit.get("work_from_home_type") or "Remote",
    }


def scrape_hiring_cafe(
    max_pages: int | None = None,
    max_jobs: int | None = None,
) -> pd.DataFrame:
    pages = max_pages if max_pages is not None else _max_pages()
    limit = max_jobs if max_jobs is not None else _max_jobs()
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    rows: list[dict[str, Any]] = []
    for page in range(1, pages + 1):
        url = _search_url(page)
        try:
            resp = session.get(url, timeout=40)
            resp.raise_for_status()
            hits = _parse_next_data(resp.text)
        except Exception:
            logger.exception("hiring.cafe page %s failed", page)
            break

        if not hits:
            logger.info("hiring.cafe page %s: no hits", page)
            break

        for hit in hits:
            mapped = _map_hit(hit)
            if mapped and is_pakistan_job_row(mapped):
                rows.append(mapped)
            if len(rows) >= limit:
                break
        if len(rows) >= limit:
            break
        time.sleep(0.6)

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows[:limit])
