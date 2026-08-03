"""RepStack careers scraper (Pakistan-friendly remote staffing).

RepStack does not use Ashby/Greenhouse/Lever. Live openings are listed on
https://repstack.co/careers/ and detail/apply pages on https://hr.repstack.co/.
BambooHR board exists but is currently empty.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = "HaunslaBot/1.0 (+https://haunsla.pk)"
CAREERS_URL = "https://repstack.co/careers/"
HR_HOST = "hr.repstack.co"
COMPANY = "RepStack"


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/json"})
    return s


def _now_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _slug_to_title(slug: str) -> str:
    text = slug.strip("/").split("/")[-1]
    text = re.sub(r"-jd.*$", "", text, flags=re.I)
    text = re.sub(r"-\d+$", "", text)
    text = text.replace("-", " ").strip()
    return text.title() if text else "RepStack Role"


def _extract_listing_links(html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    found: dict[str, dict[str, str]] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if HR_HOST not in href:
            continue
        url = href if href.startswith("http") else urljoin(CAREERS_URL, href)
        # Normalize tracking params away for dedupe key
        url_key = url.split("?")[0].rstrip("/")
        title = " ".join(a.get_text(" ", strip=True).split())
        if not title or title.lower() in {"apply now", "careers", "apply"}:
            title = _slug_to_title(url_key)
        if url_key not in found or len(title) > len(found[url_key]["title"]):
            found[url_key] = {"title": title, "job_url": url_key}
    return list(found.values())


def _parse_detail(html: str, fallback_title: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    title = fallback_title
    h1 = soup.find(["h1", "h2"])
    if h1:
        text = " ".join(h1.get_text(" ", strip=True).split())
        if text and len(text) < 120:
            title = text

    body = " ".join(soup.get_text(" ", strip=True).split())
    location = "Remote"
    # Prefer explicit Pakistan remote wording when present
    if re.search(r"pakistan\s*\(?\s*remote\s*\)?", body, flags=re.I):
        location = "Pakistan (Remote)"
    elif re.search(r"\bremote\b", body, flags=re.I):
        location = "Remote"

    job_type = "full-time"
    if re.search(r"part[\s-]?time", body, flags=re.I):
        job_type = "part-time"
    elif re.search(r"contract|freelance", body, flags=re.I):
        job_type = "contract"

    # Keep a useful description slice (not the whole marketing page)
    description = body[:8000] if body else ""
    return {
        "title": title,
        "location": location,
        "job_type": job_type,
        "description": description,
        "is_remote": True,
    }


def scrape_repstack() -> pd.DataFrame:
    session = _session()
    try:
        resp = session.get(CAREERS_URL, timeout=40)
        resp.raise_for_status()
    except Exception:
        logger.exception("RepStack careers page fetch failed")
        return pd.DataFrame()

    listings = _extract_listing_links(resp.text)
    if not listings:
        logger.warning("RepStack: no hr.repstack.co job links found on careers page")
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for item in listings:
        url = item["job_url"]
        title = item["title"]
        detail = {
            "title": title,
            "location": "Pakistan (Remote)",
            "job_type": "full-time",
            "description": "",
            "is_remote": True,
        }
        try:
            detail_resp = session.get(url, timeout=40)
            if detail_resp.ok:
                detail = _parse_detail(detail_resp.text, title)
        except Exception:
            logger.exception("RepStack detail fetch failed for %s", url)

        rows.append(
            {
                "id": None,
                "site": "repstack",
                "job_url": url,
                "job_url_direct": url,
                "title": detail["title"],
                "company": COMPANY,
                "location": detail["location"],
                "date_posted": _now_date(),
                "job_type": detail["job_type"],
                "salary_source": None,
                "interval": None,
                "min_amount": None,
                "max_amount": None,
                "currency": "PKR",
                "is_remote": True,
                "emails": None,
                "description": detail["description"],
                "company_url": "https://repstack.co/",
                "logo_photo_url": None,
            }
        )

    logger.info("RepStack scraped %s jobs", len(rows))
    return pd.DataFrame(rows) if rows else pd.DataFrame()
