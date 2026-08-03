#!/usr/bin/env python3
"""Scrape jobs from direct company career pages → merge into cache."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv(BACKEND_ROOT / ".env")

import pandas as pd  # noqa: E402

from career_page_scraper import scrape_direct_career_pages  # noqa: E402
from data_store import (  # noqa: E402
    dataframe_to_job_records,
    load_jobs_cache,
    save_jobs_cache,
    upsert_jobs,
)
from experience_level import annotate_experience_levels  # noqa: E402
from scraper import _dedupe_by_url, _filter_aggregator_jobs, _prefer_direct_url  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("scrape_career_pages")


def main() -> int:
    df = scrape_direct_career_pages()
    if df.empty:
        logger.warning("No jobs from direct career pages")
        return 1

    df = _prefer_direct_url(df)
    df = _dedupe_by_url(df)
    df = _filter_aggregator_jobs(df)
    df = annotate_experience_levels(df)

    existing = load_jobs_cache()
    if existing is not None and not existing.empty:
        merged = _dedupe_by_url(
            _prefer_direct_url(pd.concat([existing, df], ignore_index=True))
        )
    else:
        merged = df

    save_jobs_cache(merged)
    stats = upsert_jobs(dataframe_to_job_records(merged))
    logger.info(
        "Career pages kept %s; cache total %s; upsert %s",
        len(df),
        len(merged),
        stats,
    )
    if "company" in df.columns:
        logger.info(
            "Companies:\n%s",
            df["company"].astype(str).value_counts().head(20).to_string(),
        )
    if "experience_level" in df.columns:
        logger.info(
            "Experience:\n%s",
            df["experience_level"].fillna("unknown").value_counts().to_string(),
        )
    for _, row in df.head(12).iterrows():
        logger.info(
            "• %s @ %s (%s)",
            row.get("title"),
            row.get("company"),
            row.get("location"),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
