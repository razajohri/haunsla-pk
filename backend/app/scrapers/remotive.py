"""Remotive public API scraper — https://remotive.com/api/remote-jobs"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import requests

from app.scrapers.base import BaseScraper, ScrapedJob

logger = logging.getLogger(__name__)

CATEGORY_MAP = {
    "software development": "tech",
    "software-dev": "tech",
    "design": "design",
    "marketing": "marketing",
    "writing": "writing",
    "customer service": "support",
    "customer-support": "support",
    "finance": "finance",
    "devops": "tech",
    "data": "tech",
    "product": "tech",
    "qa": "tech",
}


class RemotiveScraper(BaseScraper):
    name = "remotive"
    API_URL = "https://remotive.com/api/remote-jobs"

    def fetch(self) -> list[ScrapedJob]:
        try:
            resp = requests.get(self.API_URL, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
        except Exception:
            logger.exception("Remotive scrape failed")
            return []

        jobs: list[ScrapedJob] = []
        for item in payload.get("jobs", []):
            category_raw = (item.get("category") or "").lower()
            category = CATEGORY_MAP.get(category_raw)
            if not category:
                for key, mapped in CATEGORY_MAP.items():
                    if key in category_raw:
                        category = mapped
                        break
            category = category or "tech"

            posted = None
            if item.get("publication_date"):
                try:
                    posted = datetime.fromisoformat(
                        item["publication_date"].replace("Z", "+00:00")
                    )
                except ValueError:
                    posted = datetime.now(timezone.utc)

            tags = ["Remote"]
            if item.get("job_type"):
                tags.append(item["job_type"])
            tags.append(category.title())

            jobs.append(
                ScrapedJob(
                    external_id=f"remotive-{item.get('id')}",
                    title=item.get("title") or "Untitled",
                    company=item.get("company_name") or "Unknown",
                    description=item.get("description") or "",
                    apply_url=item.get("url") or item.get("company_url") or "",
                    source=self.name,
                    category=category,
                    job_type=(item.get("job_type") or "full-time").lower().replace("_", "-"),
                    company_logo=item.get("company_logo"),
                    tags=tags,
                    posted_at=posted,
                    pakistan_friendly=True,
                )
            )
        return jobs
