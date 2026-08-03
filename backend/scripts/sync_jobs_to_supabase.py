#!/usr/bin/env python3
"""Cache-only sync: jobs_cache.pkl → Supabase upsert."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv(BACKEND_ROOT / ".env")

from data_store import (  # noqa: E402
    dataframe_to_job_records,
    load_jobs_cache,
    record_scrape_run,
    upsert_jobs,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("sync_jobs_to_supabase")


def main() -> int:
    df = load_jobs_cache()
    records = dataframe_to_job_records(df)
    result = upsert_jobs(records)
    record_scrape_run("completed", jobs_seen=len(records), message=f"cache-sync {result}")
    logger.info("Synced %s jobs: %s", len(records), result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
