#!/usr/bin/env python3
"""Standalone hiring.cafe scrape/merge into jobs_cache.pkl."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv(BACKEND_ROOT / ".env")

from data_store import load_jobs_cache, save_jobs_cache  # noqa: E402
from hiring_cafe_scraper import scrape_hiring_cafe  # noqa: E402
from scraper import _dedupe_by_url  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("scrape_hiring_cafe")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--max-jobs", type=int, default=None)
    args = parser.parse_args()

    fresh = scrape_hiring_cafe(max_pages=args.max_pages, max_jobs=args.max_jobs)
    existing = load_jobs_cache()
    if existing.empty:
        merged = fresh
    elif fresh.empty:
        merged = existing
    else:
        merged = _dedupe_by_url(pd.concat([existing, fresh], ignore_index=True))
    save_jobs_cache(merged)
    logger.info("hiring.cafe merge complete: cache=%s (+%s new scrape)", len(merged), len(fresh))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
