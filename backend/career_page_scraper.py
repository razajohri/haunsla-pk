"""Scrape jobs from company career pages (direct).

Strategy per company in config/career_pages.json:
  1. If ats + slug → Greenhouse / Ashby / Lever public APIs
  2. Fetch careers_url HTML → auto-detect embedded ATS boards
  3. Site-specific parsers (i2c ajax, tkxel job URLs, applytojob, …)
  4. Generic HTML: collect job-like links from the careers page (+ one hop)

Toggle: SCRAPE_CAREER_PAGES=1 (default on). Wired from scrape_all / career_boards.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

from ats_scraper import _fetch_ashby, _fetch_greenhouse, _fetch_lever, _row

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parent / "config" / "career_pages.json"
USER_AGENT = "HaunslaBot/1.0 (+https://haunsla.pk)"
SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    }
)

ATS_FETCHERS = {
    "greenhouse": _fetch_greenhouse,
    "ashby": _fetch_ashby,
    "lever": _fetch_lever,
}

ATS_DETECT_PATTERNS = (
    (r"boards-api\.greenhouse\.io/v1/boards/([a-z0-9-]+)", "greenhouse"),
    (r"boards\.greenhouse\.io/([a-z0-9-]+)", "greenhouse"),
    (r"job-boards\.greenhouse\.io/([a-z0-9-]+)", "greenhouse"),
    (r"api\.lever\.co/v0/postings/([a-z0-9-]+)", "lever"),
    (r"jobs\.lever\.co/([a-z0-9-]+)", "lever"),
    (r"jobs\.ashbyhq\.com/([a-z0-9-]+)", "ashby"),
    (r"api\.ashbyhq\.com/posting-api/job-board/([a-z0-9-]+)", "ashby"),
)

SKIP_LINK_TEXT = {
    "careers",
    "career",
    "jobs",
    "job",
    "apply",
    "apply now",
    "view all",
    "view all jobs",
    "view all open positions",
    "open positions",
    "see open positions",
    "join us",
    "join our team",
    "learn more",
    "read more",
    "home",
    "login",
    "sign in",
    "benefits",
    "life at",
    "why join",
    "fake job scams",
    "skip to content",
    "skip to main content",
    "skip to navigation",
    "ajax-content-wrap",
    "main-content",
    "content",
}


def _now_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _quick() -> bool:
    return os.getenv("HAUNSLA_SCRAPE_QUICK", "0") == "1"


def load_career_page_companies() -> list[dict[str, Any]]:
    if not CONFIG_PATH.exists():
        return []
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in data.get("companies") or []:
        name = (item.get("name") or "").strip()
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        out.append(
            {
                "name": name,
                "ats": (item.get("ats") or "").strip().lower() or None,
                "slug": (item.get("slug") or "").strip().lower() or None,
                "careers_url": (item.get("careers_url") or "").strip() or None,
                "parser": (item.get("parser") or "").strip().lower() or None,
                "cities": item.get("cities") or [],
                "sectors": item.get("sectors") or [],
            }
        )
    return out


def _get(url: str, *, timeout: int = 25, **kwargs) -> requests.Response | None:
    try:
        resp = SESSION.get(url, timeout=timeout, allow_redirects=True, **kwargs)
        return resp
    except Exception as exc:
        logger.warning("GET failed %s (%s)", url, type(exc).__name__)
        return None


def _detect_ats(html: str, page_url: str = "") -> list[tuple[str, str]]:
    blob = f"{page_url}\n{html}"
    found: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for pattern, ats in ATS_DETECT_PATTERNS:
        for match in re.finditer(pattern, blob, flags=re.I):
            slug = match.group(1).lower()
            if slug in {"assets", "fonts", "static", "css", "js", "api"}:
                continue
            key = (ats, slug)
            if key in seen:
                continue
            seen.add(key)
            found.append(key)
    return found


def _title_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    slug = path.split("/")[-1] if path else ""
    slug = re.sub(r"^\d+-", "", slug)
    slug = slug.replace("-", " ").replace("_", " ").strip()
    return slug.title() if slug else "Open Role"


def _is_job_link(href: str, text: str) -> bool:
    low_text = text.lower().strip()
    if not href or href.startswith("#") or href.startswith("javascript:"):
        return False
    # Fragment-only / skip-nav targets
    if href.rstrip("/").endswith(("#content", "#main-content", "#ajax-content-wrap", "#alljobs")):
        return False
    if low_text in SKIP_LINK_TEXT or any(
        low_text.startswith(s) for s in ("life at", "why ", "skip to", "view all")
    ):
        return False
    low_href = href.lower()
    markers = (
        "/job/",
        "/jobs/",
        "showjob",
        "gh_jid=",
        "greenhouse.io",
        "jobs.lever.co/",
        "ashbyhq.com/",
        "applytojob.com/apply/",
        "myworkdayjobs",
        "jobs.tkxel.com/jobs/",
    )
    # Require a concrete role URL shape — not bare /careers or /jobs index
    parsed = urlparse(href)
    path = parsed.path.rstrip("/").lower()
    query = (parsed.query or "").lower()
    has_job_query = any(
        k in query for k in ("gh_jid=", "title=", "gnk=job", "jobid=", "job_id=")
    )
    if path in {"", "/careers", "/career", "/jobs", "/job", "/join-our-team"}:
        if not has_job_query:
            return False
    concrete = (
        any(m in low_href for m in markers)
        or has_job_query
        or bool(re.search(r"applytojob\.com/apply/[A-Za-z0-9]+/.+", href, re.I))
        or bool(re.search(r"jobs\.tkxel\.com/jobs/careers/\d+/", href, re.I))
        or bool(re.search(r"/showjob/", href, re.I))
        or bool(re.search(r"hr\.repstack\.co/", href, re.I))
    )
    if not concrete:
        return False
    if low_text and 4 <= len(low_text) <= 120 and low_text not in SKIP_LINK_TEXT:
        return True
    # Empty/noise text is OK when URL clearly points at one role
    return has_job_query or bool(
        re.search(
            r"/showjob/|/apply/[A-Za-z0-9]+/[A-Za-z0-9-]+|gh_jid=|jobs\.tkxel\.com/jobs/|hr\.repstack\.co/",
            href,
            re.I,
        )
    )


def _rows_from_ats(ats: str, slug: str, company: str) -> list[dict[str, Any]]:
    fetch = ATS_FETCHERS.get(ats)
    if not fetch:
        return []
    batch = fetch(slug)
    for item in batch:
        item["company"] = company
        item["site"] = f"career_{ats}"
    return batch


def _rows_from_links(
    links: list[dict[str, str]], *, company: str, careers_url: str
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for link in links:
        url = link["job_url"].split("?")[0].rstrip("/")
        if not url or url in seen:
            continue
        seen.add(url)
        title = link.get("title") or _title_from_url(url)
        loc = link.get("location") or ""
        blob = f"{title} {loc} {url}".lower()
        remote = "remote" in blob
        pakistan = any(
            t in blob
            for t in ("pakistan", "lahore", "karachi", "islamabad", "rawalpindi")
        )
        rows.append(
            _row(
                site="career_page",
                title=title,
                company=company,
                job_url=link["job_url"],
                location=loc or ("Pakistan" if pakistan else ""),
                description=link.get("description") or f"Sourced from {careers_url}",
                is_remote=remote,
                company_url=careers_url,
                date_posted=_now_date(),
            )
        )
    return rows


def _parse_html_job_links(html: str, base_url: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    found: dict[str, dict[str, str]] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = " ".join(a.get_text(" ", strip=True).split())
        # Afiniti-style empty anchor text with title in query
        if not text and "title=" in href:
            m = re.search(r"[?&]title=([^&]+)", href)
            if m:
                text = m.group(1).replace("-", " ").replace("%20", " ")
                text = re.sub(r"^\d+\s*", "", text).strip().title()
        url = urljoin(base_url, href)
        if not _is_job_link(url, text):
            continue
        key = url.split("?")[0].rstrip("/")
        title = text if text and text.lower() not in SKIP_LINK_TEXT else _title_from_url(url)
        # Strip noisy prefixes like dates from Afiniti cards
        title = re.sub(
            r"^\d{2}/\d{2}/\d{4}\s+",
            "",
            title,
        ).strip()
        # "Karachi, Lahore | Pakistan Sr Specialist..." → keep role-ish tail
        if "|" in title and len(title) > 40:
            parts = [p.strip() for p in title.split("|")]
            title = parts[-1] if parts else title
        if key not in found or len(title) > len(found[key]["title"]):
            found[key] = {"title": title, "job_url": url}
    # Tkxel / Zoho-style absolute job URLs embedded outside <a>
    for match in re.finditer(
        r"https://jobs\.tkxel\.com/jobs/Careers/\d+/[A-Za-z0-9-]+", html
    ):
        url = match.group(0)
        key = url.rstrip("/")
        if key not in found:
            found[key] = {"title": _title_from_url(url), "job_url": url}
    return list(found.values())


def parse_i2c(company: dict[str, Any]) -> list[dict[str, Any]]:
    careers_url = company.get("careers_url") or "https://careers.i2cinc.com/careers/"
    ajax = "https://careers.i2cinc.com/ajax.php"
    try:
        resp = SESSION.post(
            ajax,
            data={"f": "getJobsPager", "filters": "{}", "s": ""},
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": careers_url,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
    except Exception:
        logger.exception("i2c ajax failed")
        return []
    html = payload.get("html") or ""
    links = _parse_html_job_links(html, careers_url)
    # Rewrite relative showjob links
    fixed: list[dict[str, str]] = []
    for link in links:
        url = link["job_url"]
        if "showjob" in url and not url.startswith("http"):
            url = urljoin(careers_url, url)
        elif url.startswith("index.php"):
            url = urljoin(careers_url, url)
        title = link["title"]
        # "Principal Data Scientist Engineering Pakistan 1 Position Apply"
        title = re.sub(
            r"\s+(Engineering|Technology|Marketing|Management|Global Operations|Payments).*$",
            "",
            title,
            flags=re.I,
        ).strip()
        loc = "Pakistan" if "pakistan" in link["title"].lower() else ""
        fixed.append({"title": title or link["title"], "job_url": url, "location": loc})
    return _rows_from_links(fixed, company=company["name"], careers_url=careers_url)


def _annotate_pk_context(rows: list[dict[str, Any]], company: dict[str, Any]) -> list[dict[str, Any]]:
    """Ensure Pakistan employer rows survive local filters when location is empty."""
    cities = company.get("cities") or []
    if not cities:
        return rows
    fallback_loc = f"{cities[0]}, Pakistan"
    for item in rows:
        loc = str(item.get("location") or "")
        blob = f"{loc} {item.get('title') or ''} {item.get('description') or ''}".lower()
        if not loc.strip():
            item["location"] = fallback_loc
        elif "pakistan" not in blob and not item.get("is_remote"):
            item["location"] = f"{loc}, Pakistan"
    return rows


def scrape_company_career_page(company: dict[str, Any]) -> list[dict[str, Any]]:
    name = company["name"]
    rows: list[dict[str, Any]] = []

    # 1) Explicit ATS
    if company.get("ats") and company.get("slug") and company["ats"] in ATS_FETCHERS:
        rows.extend(_rows_from_ats(company["ats"], company["slug"], name))
        if rows:
            return _annotate_pk_context(rows, company)

    # 2) Site-specific parser
    if company.get("parser") == "i2c":
        return _annotate_pk_context(parse_i2c(company), company)

    careers_url = company.get("careers_url")
    if not careers_url:
        return []

    resp = _get(careers_url)
    if resp is None or resp.status_code >= 400:
        logger.info("Career page skip %s status=%s", name, getattr(resp, "status_code", None))
        return []

    html = resp.text or ""
    final_url = str(resp.url)

    # 3) Auto-detect ATS embeds
    for ats, slug in _detect_ats(html, final_url):
        batch = _rows_from_ats(ats, slug, name)
        if batch:
            logger.info("Career page %s detected %s/%s → %s jobs", name, ats, slug, len(batch))
            return _annotate_pk_context(batch, company)

    # 4) HTML job links on this page
    links = _parse_html_job_links(html, final_url)

    # 5) One hop to obvious jobs listing pages
    if len(links) < 3:
        soup = BeautifulSoup(html, "lxml")
        hop_candidates: list[str] = []
        for a in soup.find_all("a", href=True):
            text = " ".join(a.get_text(" ", strip=True).split()).lower()
            href = urljoin(final_url, a["href"])
            if any(
                k in text or k in href.lower()
                for k in ("view all jobs", "/jobs", "open positions", "vacancies", "all jobs")
            ):
                hop_candidates.append(href)
        for hop in list(dict.fromkeys(hop_candidates))[:3]:
            hop_resp = _get(hop)
            if hop_resp is None or hop_resp.status_code >= 400:
                continue
            # ATS on hop page?
            for ats, slug in _detect_ats(hop_resp.text, str(hop_resp.url)):
                batch = _rows_from_ats(ats, slug, name)
                if batch:
                    return _annotate_pk_context(batch, company)
            links.extend(_parse_html_job_links(hop_resp.text, str(hop_resp.url)))
            time.sleep(0.1)

    # Dedupe links
    deduped: dict[str, dict[str, str]] = {}
    for link in links:
        key = link["job_url"].split("?")[0].rstrip("/")
        deduped[key] = link
    rows = _rows_from_links(list(deduped.values()), company=name, careers_url=careers_url)
    return _annotate_pk_context(rows, company)


def scrape_direct_career_pages(
    *,
    limit: int | None = None,
    delay_sec: float = 0.12,
) -> pd.DataFrame:
    if os.getenv("SCRAPE_CAREER_PAGES", "1") != "1":
        logger.info("Direct career pages skipped (SCRAPE_CAREER_PAGES!=1)")
        return pd.DataFrame()

    companies = load_career_page_companies()
    if limit is None:
        limit = int(os.getenv("CAREER_PAGE_LIMIT", "25" if _quick() else "0") or 0)
    if limit > 0:
        companies = companies[:limit]

    logger.info("Scraping %s direct company career pages", len(companies))
    rows: list[dict[str, Any]] = []
    by_company: dict[str, int] = {}

    for idx, company in enumerate(companies, start=1):
        try:
            batch = scrape_company_career_page(company)
        except Exception:
            logger.exception("Career page failed for %s", company.get("name"))
            batch = []
        by_company[company["name"]] = len(batch)
        rows.extend(batch)
        if idx % 10 == 0 or idx == len(companies):
            logger.info(
                "Career pages progress %s/%s rows=%s",
                idx,
                len(companies),
                len(rows),
            )
        if delay_sec:
            time.sleep(delay_sec)

    nonempty = {k: v for k, v in by_company.items() if v}
    logger.info(
        "Direct career pages: %s jobs from %s/%s companies with listings",
        len(rows),
        len(nonempty),
        len(companies),
    )
    if nonempty:
        top = sorted(nonempty.items(), key=lambda kv: -kv[1])[:12]
        logger.info("Top career-page companies: %s", top)
    return pd.DataFrame(rows) if rows else pd.DataFrame()
