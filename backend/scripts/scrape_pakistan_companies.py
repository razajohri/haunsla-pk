#!/usr/bin/env python3
"""Scrape Lahore / Karachi / Islamabad employers → merge into jobs cache.

Focus: graduate / junior / trainee roles in tech, business, marketing, finance, banks.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv(BACKEND_ROOT / ".env")

from data_store import (  # noqa: E402
    dataframe_to_job_records,
    load_jobs_cache,
    save_jobs_cache,
    upsert_jobs,
)
from experience_level import annotate_experience_levels  # noqa: E402
from pakistan_companies import load_pakistan_companies, scrape_pakistan_employers  # noqa: E402
from scraper import _dedupe_by_url, _filter_aggregator_jobs, _prefer_direct_url  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("scrape_pakistan_companies")


def main() -> int:
    companies = load_pakistan_companies()
    logger.info(
        "Companies in config: %s (set PK_COMPANY_LIMIT to cap Indeed company queries)",
        len(companies),
    )
    df = scrape_pakistan_employers()
    if df.empty:
        logger.warning("No rows from Pakistan employer scrape")
        return 1

    df = _prefer_direct_url(df)
    df = _dedupe_by_url(df)
    df = _filter_aggregator_jobs(df)
    df = annotate_experience_levels(df)

    existing = load_jobs_cache()
    if existing is not None and not existing.empty:
        merged = _dedupe_by_url(
            _prefer_direct_url(pd_concat(existing, df))
        )
    else:
        merged = df

    save_jobs_cache(merged)
    stats = upsert_jobs(dataframe_to_job_records(merged))
    logger.info(
        "PK scrape kept %s new-filtered rows; cache total %s; upsert %s",
        len(df),
        len(merged),
        stats,
    )
    if not df.empty and "experience_level" in df.columns:
        logger.info(
            "PK experience mix:\n%s",
            df["experience_level"].fillna("unknown").value_counts().to_string(),
        )
    if "company" in df.columns:
        logger.info(
            "Top companies:\n%s",
            df["company"].astype(str).value_counts().head(15).to_string(),
        )
    return 0


def pd_concat(a, b):
    import pandas as pd

    return pd.concat([a, b], ignore_index=True)


if __name__ == "__main__":
    raise SystemExit(main())
