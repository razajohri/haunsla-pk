#!/usr/bin/env python3
"""Soft-deactivate jobs whose apply URLs are dead."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv(BACKEND_ROOT / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("validate_job_links")

USER_AGENT = "HaunslaBot/1.0 (+https://haunsla.pk; link-validator)"


def _supabase():
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_KEY", "").strip()
    )
    if not url or not key:
        return None
    from supabase import create_client

    return create_client(url, key)


def check_url(url: str, timeout: float = 12.0) -> str:
    """Return ok | dead | unknown."""
    if not url:
        return "dead"
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.head(url, allow_redirects=True, timeout=timeout, headers=headers)
        if resp.status_code == 405:
            resp = requests.get(url, allow_redirects=True, timeout=timeout, headers=headers, stream=True)
            resp.close()
        if resp.status_code == 404:
            return "dead"
        if resp.status_code in {401, 403, 429}:
            return "unknown"
        if 200 <= resp.status_code < 400:
            return "ok"
        if resp.status_code >= 500:
            return "unknown"
        return "dead"
    except requests.RequestException:
        return "unknown"


def fetch_active_jobs(client, limit: int = 2000) -> list[dict[str, Any]]:
    result = (
        client.table("jobs")
        .select("id,source_key,job_url,job_url_direct,site,is_active")
        .eq("is_active", True)
        .limit(limit)
        .execute()
    )
    return result.data or []


def deactivate(client, job_id: str) -> None:
    client.table("jobs").update({"is_active": False}).eq("id", job_id).execute()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--prune-unknown-aggregators", action="store_true")
    parser.add_argument("--limit", type=int, default=2000)
    args = parser.parse_args()

    client = _supabase()
    if client is None:
        logger.warning("No Supabase credentials; skipping link validation")
        return 0

    jobs = fetch_active_jobs(client, limit=args.limit)
    logger.info("Validating %s active jobs with %s workers", len(jobs), args.workers)

    dead = 0
    unknown = 0

    def work(job: dict[str, Any]) -> tuple[str, str]:
        url = job.get("job_url_direct") or job.get("job_url") or ""
        return job["id"], check_url(url)

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(work, job) for job in jobs]
        for fut in as_completed(futures):
            job_id, status = fut.result()
            job = next(j for j in jobs if j["id"] == job_id)
            site = (job.get("site") or "").lower()
            if status == "dead":
                deactivate(client, job_id)
                dead += 1
            elif status == "unknown" and args.prune_unknown_aggregators and site in {
                "indeed",
                "google",
            }:
                deactivate(client, job_id)
                unknown += 1

    logger.info("Deactivated dead=%s unknown_pruned=%s", dead, unknown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
