#!/usr/bin/env python3
"""Full refresh: scrape → pickle → Supabase upsert → link validate."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv(BACKEND_ROOT / ".env")

from data_store import (  # noqa: E402
    dataframe_to_job_records,
    record_scrape_run,
    save_jobs_cache,
    upsert_jobs,
)
from scraper import scrape_all  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("update_jobs_cache")


def main() -> int:
    try:
        df = scrape_all(" ")
        if "job_url_direct" in df.columns and "job_url" in df.columns:
            df = df.copy()
            df["job_url"] = df["job_url_direct"].fillna(df["job_url"])
        if not df.empty:
            url_col = "job_url_direct" if "job_url_direct" in df.columns else "job_url"
            df = df[df[url_col].notna() & (df[url_col].astype(str).str.len() > 0)]

        save_jobs_cache(df)
        records = dataframe_to_job_records(df)
        result = upsert_jobs(records)
        record_scrape_run("completed", jobs_seen=len(records), message=str(result))

        validate = BACKEND_ROOT / "scripts" / "validate_job_links.py"
        if validate.exists() and os.getenv("SKIP_LINK_VALIDATE", "0") != "1":
            subprocess.run(
                [
                    sys.executable,
                    str(validate),
                    "--workers",
                    os.getenv("VALIDATE_WORKERS", "12"),
                    "--prune-unknown-aggregators",
                ],
                check=False,
                cwd=str(BACKEND_ROOT),
            )
        logger.info("Update complete: %s jobs", len(records))
        return 0
    except Exception as exc:
        logger.exception("update_jobs_cache failed")
        record_scrape_run("failed", jobs_seen=0, message=str(exc))
        raise


if __name__ == "__main__":
    raise SystemExit(main())
