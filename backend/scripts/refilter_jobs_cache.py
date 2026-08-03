#!/usr/bin/env python3
"""Re-apply Pakistan / worldwide-remote filter to jobs_cache.pkl."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from ats_location import filter_dataframe  # noqa: E402
from data_store import load_jobs_cache, save_jobs_cache  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("refilter_jobs_cache")


def main() -> int:
    df = load_jobs_cache()
    before = len(df)
    filtered = filter_dataframe(df)
    save_jobs_cache(filtered)
    logger.info("Refiltered cache %s → %s", before, len(filtered))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
