#!/usr/bin/env python3
"""Deactivate Supabase rows that fail Pakistan / worldwide-remote rules."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv(BACKEND_ROOT / ".env")

from ats_location import is_pakistan_job_row  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("purge_non_pakistan")


def main() -> int:
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_KEY", "").strip()
    )
    if not url or not key:
        logger.error("SUPABASE_URL + service role key required")
        return 1

    from supabase import create_client

    client = create_client(url, key)
    result = (
        client.table("jobs")
        .select("id,title,company,location,description,is_remote,site,is_active")
        .eq("is_active", True)
        .limit(5000)
        .execute()
    )
    rows = result.data or []
    deactivated = 0
    for row in rows:
        if not is_pakistan_job_row(row):
            client.table("jobs").update({"is_active": False}).eq("id", row["id"]).execute()
            deactivated += 1
    logger.info("Checked %s active jobs; deactivated %s", len(rows), deactivated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
