"""Company → career-page scrape across multiple ATS types.

Reads config/worldwide_companies.json and fetches each company's board
(Ashby / Greenhouse / Lever). This is the “find companies, then careers”
path (not a single aggregator dump).
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import pandas as pd

from ats_scraper import _fetch_ashby, _fetch_greenhouse, _fetch_lever
from worldwide_remote import filter_worldwide

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parent / "config" / "worldwide_companies.json"
FETCHERS = {
    "greenhouse": _fetch_greenhouse,
    "ashby": _fetch_ashby,
    "lever": _fetch_lever,
}


def load_worldwide_companies() -> list[dict[str, str]]:
    if not CONFIG_PATH.exists():
        return []
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    companies = data.get("companies") or []
    out: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in companies:
        ats = (item.get("ats") or "").strip().lower()
        slug = (item.get("slug") or "").strip().lower()
        if ats not in FETCHERS or not slug:
            continue
        key = (ats, slug)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "name": item.get("name") or slug,
                "ats": ats,
                "slug": slug,
            }
        )
    return out


def scrape_worldwide_career_boards(
    *,
    worldwide_only: bool = True,
    delay_sec: float = 0.08,
) -> pd.DataFrame:
    companies = load_worldwide_companies()
    logger.info("Career boards: scraping %s worldwide companies", len(companies))
    rows: list[dict[str, Any]] = []
    by_ats: dict[str, int] = {}

    for idx, company in enumerate(companies, start=1):
        fetch = FETCHERS[company["ats"]]
        try:
            batch = fetch(company["slug"])
        except Exception:
            logger.exception(
                "Career board failed ats=%s slug=%s", company["ats"], company["slug"]
            )
            batch = []
        # Prefer board company name when fetch used slug title-case
        for item in batch:
            if not item.get("company") or item["company"].lower() == company["slug"]:
                item["company"] = company["name"]
            # Tag source site as the ATS (already set) — keep
            rows.append(item)
        by_ats[company["ats"]] = by_ats.get(company["ats"], 0) + len(batch)
        if idx % 25 == 0 or idx == len(companies):
            logger.info(
                "Career boards progress %s/%s rows=%s",
                idx,
                len(companies),
                len(rows),
            )
        if delay_sec:
            time.sleep(delay_sec)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    # Keep remote-looking rows first
    if "is_remote" in df.columns:
        df = df[df["is_remote"].fillna(False).astype(bool) | df["location"].astype(str).str.contains("remote", case=False, na=False)]
    if worldwide_only:
        before = len(df)
        df = filter_worldwide(df)
        logger.info(
            "Career boards worldwide filter %s → %s (by ats pre-filter %s)",
            before,
            len(df),
            by_ats,
        )
    else:
        logger.info("Career boards scraped %s (by ats %s)", len(df), by_ats)
    return df.reset_index(drop=True)
