"""Scrape graduate-friendly jobs from Pakistan employers (LHE / KHI / ISB).

Sources:
  1. Optional ATS boards for companies with greenhouse/ashby/lever slugs
  2. Indeed city + field queries (tech, business, marketing, finance, banks)
  3. Indeed per-company queries (from config/pakistan_companies.json)

Toggle with SCRAPE_PAKISTAN_COMPANIES=1 (default on).
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parent / "config" / "pakistan_companies.json"

PK_CITIES = ("Lahore", "Karachi", "Islamabad")

# Graduate / early-career terms across fields the user cares about
FIELD_TERMS = (
    # Tech
    "software engineer graduate",
    "junior software developer",
    "fresh graduate IT",
    "internship software",
    "junior web developer",
    "data analyst graduate",
    "QA trainee",
    "associate software engineer",
    # Business
    "management trainee",
    "graduate trainee program",
    "business analyst graduate",
    "fresh graduate business",
    "operations trainee",
    # Marketing
    "marketing intern",
    "digital marketing graduate",
    "fresh graduate marketing",
    "junior marketing executive",
    "social media intern",
    # Finance / banks
    "bank graduate trainee",
    "management trainee bank",
    "fresh graduate finance",
    "junior accountant",
    "finance intern",
    "credit analyst trainee",
    "relationship manager trainee",
    "Islamic banking graduate",
)

COMPANY_QUERY_TEMPLATES = (
    "{name} graduate",
    "{name} intern",
    "{name} trainee",
    "{name} junior",
)


def _quick() -> bool:
    return os.getenv("HAUNSLA_SCRAPE_QUICK", "0") == "1"


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def load_pakistan_companies(
    *,
    cities: Iterable[str] | None = None,
    sectors: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    if not CONFIG_PATH.exists():
        logger.warning("Missing %s", CONFIG_PATH)
        return []
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    companies = data.get("companies") or []
    city_filter = {c.strip().lower() for c in cities} if cities else None
    sector_filter = {s.strip().lower() for s in sectors} if sectors else None
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in companies:
        name = (item.get("name") or "").strip()
        if not name or name.lower() in seen:
            continue
        item_cities = [str(c) for c in (item.get("cities") or PK_CITIES)]
        item_sectors = [str(s).lower() for s in (item.get("sectors") or [])]
        if city_filter and not any(c.lower() in city_filter for c in item_cities):
            continue
        if sector_filter and not any(s in sector_filter for s in item_sectors):
            continue
        seen.add(name.lower())
        out.append(
            {
                "name": name,
                "cities": item_cities,
                "sectors": item_sectors,
                "ats": (item.get("ats") or "").strip().lower() or None,
                "slug": (item.get("slug") or "").strip().lower() or None,
                "aliases": [str(a) for a in (item.get("aliases") or [])],
            }
        )
    return out


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
        logger.exception(
            "PK JobSpy scrape failed term=%r loc=%r",
            kwargs.get("search_term") or kwargs.get("google_search_term"),
            kwargs.get("location"),
        )
        return pd.DataFrame()


def scrape_pakistan_ats_boards(companies: list[dict[str, Any]] | None = None) -> pd.DataFrame:
    """Fetch Greenhouse/Ashby/Lever for PK companies that have ATS slugs."""
    from ats_scraper import _fetch_ashby, _fetch_greenhouse, _fetch_lever

    fetchers = {
        "greenhouse": _fetch_greenhouse,
        "ashby": _fetch_ashby,
        "lever": _fetch_lever,
    }
    companies = companies if companies is not None else load_pakistan_companies()
    rows: list[dict[str, Any]] = []
    for company in companies:
        ats = company.get("ats")
        slug = company.get("slug")
        if not ats or not slug or ats not in fetchers:
            continue
        try:
            batch = fetchers[ats](slug)
        except Exception:
            logger.exception("PK ATS failed %s/%s", ats, slug)
            batch = []
        for item in batch:
            item["company"] = company["name"]
            item.setdefault("site", ats)
            rows.append(item)
        time.sleep(0.05)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def scrape_pakistan_city_fields(
    *,
    cities: Iterable[str] | None = None,
    terms: Iterable[str] | None = None,
    results_wanted: int | None = None,
) -> pd.DataFrame:
    """Indeed: graduate roles by city × field (tech/business/marketing/finance/banks)."""
    wanted = results_wanted or _int_env(
        "PK_CITY_RESULTS_PER_QUERY", 40 if _quick() else 120
    )
    city_list = list(cities) if cities is not None else list(PK_CITIES)
    term_list = list(terms) if terms is not None else list(FIELD_TERMS)
    if _quick():
        city_list = city_list[:2]
        term_list = term_list[:6]

    frames: list[pd.DataFrame] = []
    for city in city_list:
        for term in term_list:
            logger.info("PK city Indeed term=%r location=%s", term, city)
            df = _safe_scrape_jobs(
                site_name=["indeed"],
                search_term=term,
                is_remote=False,
                country_indeed="Pakistan",
                location=city,
                results_wanted=wanted,
                verbose=0,
            )
            if not df.empty:
                if "location" not in df.columns or df["location"].isna().all():
                    df = df.copy()
                    df["location"] = city + ", Pakistan"
                frames.append(df)
            time.sleep(0.15)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def scrape_pakistan_company_indeed(
    companies: list[dict[str, Any]] | None = None,
    *,
    results_wanted: int | None = None,
) -> pd.DataFrame:
    """Indeed: search each employer for graduate / intern / junior roles."""
    companies = companies if companies is not None else load_pakistan_companies()
    limit = _int_env("PK_COMPANY_LIMIT", 40 if _quick() else 0)
    # 0 = all companies
    if limit > 0:
        companies = companies[:limit]

    wanted = results_wanted or _int_env(
        "PK_COMPANY_RESULTS_PER_QUERY", 25 if _quick() else 60
    )
    # Prefer banks + tech first when limiting isn't set but quick mode is
    if _quick():
        priority = {"banking", "finance", "tech", "fintech"}
        companies = sorted(
            companies,
            key=lambda c: 0 if set(c.get("sectors") or []) & priority else 1,
        )[:limit or 40]

    templates = COMPANY_QUERY_TEMPLATES[:2] if _quick() else COMPANY_QUERY_TEMPLATES[:2]
    frames: list[pd.DataFrame] = []
    for idx, company in enumerate(companies, start=1):
        names = [company["name"], *company.get("aliases", [])]
        cities = company.get("cities") or list(PK_CITIES)
        city = cities[0]
        for name in names[:1]:
            for tmpl in templates:
                term = tmpl.format(name=name)
                logger.info(
                    "PK company Indeed %s/%s term=%r city=%s",
                    idx,
                    len(companies),
                    term,
                    city,
                )
                df = _safe_scrape_jobs(
                    site_name=["indeed"],
                    search_term=term,
                    is_remote=False,
                    country_indeed="Pakistan",
                    location=city,
                    results_wanted=wanted,
                    verbose=0,
                )
                if not df.empty:
                    frames.append(df)
                time.sleep(0.12)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def scrape_pakistan_google(results_wanted: int | None = None) -> pd.DataFrame:
    wanted = results_wanted or _int_env("PK_GOOGLE_RESULTS", 30 if _quick() else 80)
    terms = [
        "fresh graduate jobs Lahore",
        "fresh graduate jobs Karachi",
        "fresh graduate jobs Islamabad",
        "management trainee bank Pakistan",
        "software engineer junior Lahore",
        "internship marketing Karachi",
        "graduate trainee program Pakistan",
        "associate software engineer Islamabad",
        "digital marketing intern Lahore",
        "finance intern Karachi",
        "IT jobs for fresh graduates Pakistan",
        "bank jobs for fresh graduates Pakistan",
    ]
    if _quick():
        terms = terms[:4]
    frames: list[pd.DataFrame] = []
    for term in terms:
        logger.info("PK Google term=%r", term)
        df = _safe_scrape_jobs(
            site_name=["google"],
            google_search_term=term,
            results_wanted=wanted,
            verbose=0,
        )
        if not df.empty:
            frames.append(df)
        time.sleep(0.1)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def scrape_pakistan_employers() -> pd.DataFrame:
    """Full Pakistan employer pass used by scrape_all."""
    if os.getenv("SCRAPE_PAKISTAN_COMPANIES", "1") != "1":
        logger.info("Pakistan companies scrape skipped (SCRAPE_PAKISTAN_COMPANIES!=1)")
        return pd.DataFrame()

    companies = load_pakistan_companies()
    logger.info("Loaded %s Pakistan companies from config", len(companies))

    frames: list[pd.DataFrame] = []
    try:
        frames.append(scrape_pakistan_ats_boards(companies))
    except Exception:
        logger.exception("PK ATS boards failed")

    try:
        frames.append(scrape_pakistan_city_fields())
    except Exception:
        logger.exception("PK city field scrape failed")

    try:
        frames.append(scrape_pakistan_company_indeed(companies))
    except Exception:
        logger.exception("PK company Indeed scrape failed")

    if os.getenv("SCRAPE_PAKISTAN_GOOGLE", "1") == "1":
        try:
            frames.append(scrape_pakistan_google())
        except Exception:
            logger.exception("PK Google scrape failed")

    nonempty = [f for f in frames if f is not None and not f.empty]
    if not nonempty:
        return pd.DataFrame()
    df = pd.concat(nonempty, ignore_index=True)
    logger.info("Pakistan employers scrape raw rows=%s", len(df))
    return df
