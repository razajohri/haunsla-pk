#!/usr/bin/env python3
"""Apply backend/db/schema.sql using DATABASE_URL."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv(BACKEND_ROOT / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("apply_schema")


def main() -> int:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        logger.error("DATABASE_URL is required")
        return 1
    if database_url.startswith("sqlite"):
        logger.error("apply_schema.py targets Postgres/Supabase, not SQLite")
        return 1

    schema_path = BACKEND_ROOT / "db" / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")

    import psycopg2

    with psycopg2.connect(database_url) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql)
    logger.info("Applied schema from %s", schema_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
