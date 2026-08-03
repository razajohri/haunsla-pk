"""Haunsla job scrape orchestration (ported from remotejobscanada.ca).

Pipeline:
  ATS (Ashby/Greenhouse/Lever) + Indeed + Google (+ optional hiring.cafe)
    → Pakistan / worldwide-remote filter
    → URL dedupe
    → jobs_cache.pkl
"""

from __future__ import annotations

import logging
import os
from typing import Iterable

import pandas as pd

from ats_location import filter_dataframe
from ats_scraper import scrape_ats

logger = logging.getLogger(__name__)

# --- Tunables (Canada playbook defaults; override via env) -----------------

def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


QUICK = os.getenv("HAUNSLA_SCRAPE_QUICK", "0") == "1"

INDEED_RESULTS_PER_QUERY = _int_env(
    "INDEED_RESULTS_PER_QUERY", 100 if QUICK else 1500
)
ATS_RESULTS_WANTED = _int_env("ATS_RESULTS_WANTED", 200 if QUICK else 10000)
GOOGLE_RESULTS_WANTED = _int_env("GOOGLE_RESULTS_WANTED", 50 if QUICK else 1000)
ATS_HOURS_OLD = _int_env("ATS_HOURS_OLD", 336)  # 14 days
# Keyword-filter ATS boards (reduces volume). Off by default for bulk fills.
ATS_KEYWORD_FILTER = os.getenv("ATS_KEYWORD_FILTER", "0") == "1"

LISTED_JOB_SITES = (
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
)
WORLDWIDE_ONLY = os.getenv("WORLDWIDE_ONLY", "0") == "1"

ATS_SEARCH_TERMS = (
    "remote",
    "writer",
    "content",
    "copywriter",
    "editor",
    "communications",
    "marketing",
    "engineer",
    "developer",
    "designer",
    "support",
)

INDEED_SEARCH_TERMS = (
    "",
    "software",
    "engineer",
    "developer",
    "analyst",
    "manager",
    "sales",
    "marketing",
    "customer service",
    "support",
    "designer",
    "writer",
    "content writer",
    "data",
    "product",
    "devops",
    "python",
    "javascript",
    "react",
    "remote",
    "fullstack",
    "frontend",
    "backend",
    "qa",
    "accountant",
    "hr",
    "recruiter",
    "project manager",
    "business analyst",
    "ai",
    "machine learning",
)

GOOGLE_SEARCH_TERMS = (
    "remote jobs Pakistan",
    "remote jobs worldwide",
    "remote software engineer jobs",
    "remote developer jobs",
    "work from anywhere jobs",
)


def _safe_scrape_jobs(**kwargs) -> pd.DataFrame:
    try:
        from jobspy import scrape_jobs
    except ImportError:
        logger.error("python-jobspy is not installed")
        return pd.DataFrame()
    try:
        df = scrape_jobs(**kwargs)
        if df is None:
            return pd.DataFrame()
        return df
    except Exception:
        logger.exception("JobSpy scrape failed kwargs=%s", {k: kwargs.get(k) for k in ("site_name", "search_term", "google_search_term", "country_indeed")})
        return pd.DataFrame()


def scrape_indeed(
    terms: Iterable[str] | None = None,
    *,
    country_indeed: str = "Pakistan",
    location: str = "Pakistan",
    results_wanted: int | None = None,
) -> pd.DataFrame:
    """Indeed remote scrape. Do NOT pass hours_old (JobSpy conflict)."""
    wanted = results_wanted or INDEED_RESULTS_PER_QUERY
    frames: list[pd.DataFrame] = []
    search_terms = list(terms) if terms is not None else list(INDEED_SEARCH_TERMS)
    if QUICK:
        search_terms = search_terms[:3]

    for term in search_terms:
        logger.info("Indeed scrape term=%r country=%s", term, country_indeed)
        df = _safe_scrape_jobs(
            site_name=["indeed"],
            search_term=term or None,
            is_remote=True,
            country_indeed=country_indeed,
            location=location,
            results_wanted=wanted,
            verbose=0,
        )
        if not df.empty:
            frames.append(df)

    # Optional second pass: major Indeed locales → later filtered to open remote
    if os.getenv("SCRAPE_INDEED_INTL", "1") == "1":
        intl_terms = (
            search_terms[:2]
            if QUICK
            else ("", "software", "engineer", "developer", "writer", "support", "data", "marketing")
        )
        intl_countries = (
            [("USA", "Remote")]
            if QUICK
            else [
                ("USA", "Remote"),
                ("UK", "Remote"),
                ("Canada", "Remote"),
            ]
        )
        for country, loc in intl_countries:
            for term in intl_terms:
                logger.info("Indeed intl scrape term=%r country=%s", term, country)
                df = _safe_scrape_jobs(
                    site_name=["indeed"],
                    search_term=term or None,
                    is_remote=True,
                    country_indeed=country,
                    location=loc,
                    results_wanted=min(wanted, 800 if not QUICK else 50),
                    verbose=0,
                )
                if not df.empty:
                    frames.append(df)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def scrape_google(
    terms: Iterable[str] | None = None,
    results_wanted: int | None = None,
) -> pd.DataFrame:
    wanted = results_wanted or GOOGLE_RESULTS_WANTED
    frames: list[pd.DataFrame] = []
    search_terms = list(terms) if terms is not None else list(GOOGLE_SEARCH_TERMS)
    if QUICK:
        search_terms = search_terms[:1]
    for term in search_terms:
        logger.info("Google scrape term=%r", term)
        df = _safe_scrape_jobs(
            site_name=["google"],
            google_search_term=term,
            results_wanted=wanted,
            verbose=0,
        )
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def scrape_linkedin(results_wanted: int = 200) -> pd.DataFrame:
    """LinkedIn remote via JobSpy (another source beyond Indeed/Greenhouse)."""
    if os.getenv("SCRAPE_LINKEDIN", "1") != "1":
        return pd.DataFrame()
    wanted = 40 if QUICK else results_wanted
    terms = ("remote", "software engineer", "developer", "designer", "writer", "support")
    if QUICK:
        terms = terms[:2]
    frames: list[pd.DataFrame] = []
    for term in terms:
        logger.info("LinkedIn scrape term=%r", term)
        df = _safe_scrape_jobs(
            site_name=["linkedin"],
            search_term=term,
            is_remote=True,
            results_wanted=wanted,
            hours_old=168,
            verbose=0,
        )
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def scrape_bayt_naukri(results_wanted: int = 200) -> pd.DataFrame:
    """Optional regional JobSpy boards (Bayt / Naukri)."""
    if os.getenv("SCRAPE_BAYT_NAUKRI", "0") != "1":
        return pd.DataFrame()
    frames: list[pd.DataFrame] = []
    for site, country, location in (
        ("bayt", "Pakistan", "Pakistan"),
        ("naukri", "India", "India"),
    ):
        logger.info("Regional scrape site=%s", site)
        df = _safe_scrape_jobs(
            site_name=[site],
            search_term="remote",
            is_remote=True,
            country_indeed=country,
            location=location,
            results_wanted=results_wanted if not QUICK else 40,
            verbose=0,
        )
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def scrape_legacy_boards() -> pd.DataFrame:
    """Keep Remotive + We Work Remotely as first-party sources."""
    rows: list[dict] = []
    try:
        from app.scrapers.remotive import RemotiveScraper
        from app.scrapers.weworkremotely import WeWorkRemotelyScraper

        for scraper in (RemotiveScraper(), WeWorkRemotelyScraper()):
            for item in scraper.fetch():
                if not item.apply_url:
                    continue
                rows.append(
                    {
                        "id": None,
                        "site": scraper.name,
                        "job_url": item.apply_url,
                        "job_url_direct": item.apply_url,
                        "title": item.title,
                        "company": item.company,
                        "location": "Remote",
                        "date_posted": (
                            item.posted_at.date().isoformat()
                            if item.posted_at
                            else None
                        ),
                        "job_type": item.job_type,
                        "salary_source": None,
                        "interval": None,
                        "min_amount": item.salary_min,
                        "max_amount": item.salary_max,
                        "currency": item.salary_currency or "USD",
                        "is_remote": True,
                        "emails": None,
                        "description": item.description,
                        "company_url": None,
                        "logo_photo_url": item.company_logo,
                    }
                )
    except Exception:
        logger.exception("Legacy Remotive/WWR scrape failed")
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _prefer_direct_url(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if "job_url_direct" in out.columns and "job_url" in out.columns:
        out["job_url"] = out["job_url_direct"].fillna(out["job_url"])
    return out


def _dedupe_by_url(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if "job_url_direct" in out.columns:
        key = out["job_url_direct"].fillna(out.get("job_url"))
    else:
        key = out.get("job_url")
    out = out.assign(_dedupe_url=key)
    out = out[out["_dedupe_url"].notna() & (out["_dedupe_url"].astype(str).str.len() > 0)]
    out = out.drop_duplicates(subset=["_dedupe_url"], keep="first")
    return out.drop(columns=["_dedupe_url"]).reset_index(drop=True)


def _filter_aggregator_jobs(df: pd.DataFrame) -> pd.DataFrame:
    df = filter_dataframe(df)
    if WORLDWIDE_ONLY:
        from worldwide_remote import filter_worldwide

        before = len(df)
        df = filter_worldwide(df)
        logger.info("Worldwide-only filter %s → %s", before, len(df))
    return df


def scrape_all(search_term: str = " ") -> pd.DataFrame:
    """Full refresh scrape used by scripts/update_jobs_cache.py.

    Diversified sources:
    - Company career boards (Ashby/GH/Lever from worldwide_companies.json)
    - Remote aggregators (RemoteOK, Jobicy, Arbeitnow, Himalayas)
    - Remotive + multi-category We Work Remotely
    - Indeed / Google / LinkedIn (JobSpy)
    - RepStack (Pakistan remote staffing)
    """
    del search_term  # Canada API accepted a dummy term; unused here
    frames: list[pd.DataFrame] = []

    # 1) Company → career page path (multi-ATS)
    if os.getenv("SCRAPE_CAREER_BOARDS", "1") == "1":
        try:
            from career_boards import scrape_worldwide_career_boards

            logger.info("Scraping worldwide company career boards")
            frames.append(
                scrape_worldwide_career_boards(worldwide_only=WORLDWIDE_ONLY)
            )
        except Exception:
            logger.exception("Career boards scrape failed")

    # 2) Large ATS slug lists (existing Haunsla/Canada-style bulk)
    if os.getenv("SCRAPE_ATS_BULK", "1") == "1":
        logger.info("Scraping bulk ATS boards")
        if ATS_KEYWORD_FILTER:
            ats_terms = ATS_SEARCH_TERMS[:3] if QUICK else ATS_SEARCH_TERMS
        else:
            ats_terms = ("remote",)
        frames.append(
            scrape_ats(search_terms=ats_terms, results_wanted=ATS_RESULTS_WANTED)
        )

    # 3) Remote-native aggregators (great for worldwide)
    if os.getenv("SCRAPE_REMOTE_BOARDS", "1") == "1":
        try:
            from remote_boards import scrape_remote_boards

            logger.info("Scraping RemoteOK / Jobicy / Arbeitnow / Himalayas")
            frames.append(scrape_remote_boards())
        except Exception:
            logger.exception("Remote boards scrape failed")

    # 4) Legacy Remotive + WWR (multi-category)
    frames.append(scrape_legacy_boards())

    # 5) JobSpy aggregators
    if os.getenv("SCRAPE_INDEED", "1") == "1":
        logger.info("Scraping Indeed")
        frames.append(scrape_indeed())

    if os.getenv("SCRAPE_GOOGLE", "1") == "1":
        logger.info("Scraping Google Jobs")
        frames.append(scrape_google())

    frames.append(scrape_linkedin())
    frames.append(scrape_bayt_naukri())

    if os.getenv("SCRAPE_REPSTACK", "1") == "1":
        try:
            from repstack_scraper import scrape_repstack

            logger.info("Scraping RepStack careers")
            frames.append(scrape_repstack())
        except Exception:
            logger.exception("RepStack scrape failed")

    if os.getenv("SCRAPE_HIRING_CAFE", "0") == "1":
        try:
            from hiring_cafe_scraper import scrape_hiring_cafe

            logger.info("Scraping hiring.cafe")
            frames.append(scrape_hiring_cafe())
        except Exception:
            logger.exception("hiring.cafe scrape failed")

    nonempty = [f for f in frames if f is not None and not f.empty]
    if not nonempty:
        logger.warning("scrape_all produced zero rows")
        return pd.DataFrame()

    df = pd.concat(nonempty, ignore_index=True)
    df = _prefer_direct_url(df)
    df = _dedupe_by_url(df)
    df = _filter_aggregator_jobs(df)
    if "site" in df.columns:
        logger.info("Source mix:\n%s", df["site"].astype(str).str.lower().value_counts().to_string())
    logger.info("scrape_all kept %s jobs after filter/dedupe", len(df))
    return df
