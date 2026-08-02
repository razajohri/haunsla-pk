"""We Work Remotely RSS scraper."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from xml.etree import ElementTree

import requests

from app.scrapers.base import BaseScraper, ScrapedJob

logger = logging.getLogger(__name__)


def _guess_category(title: str, tags: str) -> str:
    text = f"{title} {tags}".lower()
    rules = [
        ("design", "design"),
        ("marketing", "marketing"),
        ("writ", "writing"),
        ("support", "support"),
        ("customer", "support"),
        ("finance", "finance"),
        ("account", "finance"),
    ]
    for needle, category in rules:
        if needle in text:
            return category
    return "tech"


class WeWorkRemotelyScraper(BaseScraper):
    name = "weworkremotely"
    FEED_URL = "https://weworkremotely.com/categories/remote-programming-jobs.rss"

    def fetch(self) -> list[ScrapedJob]:
        try:
            resp = requests.get(
                self.FEED_URL,
                timeout=30,
                headers={"User-Agent": "HaunslaBot/0.1 (+https://haunsla.pk)"},
            )
            resp.raise_for_status()
            root = ElementTree.fromstring(resp.content)
        except Exception:
            logger.exception("We Work Remotely scrape failed")
            return []

        channel = root.find("channel")
        if channel is None:
            return []

        jobs: list[ScrapedJob] = []
        for item in channel.findall("item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            description = item.findtext("description") or ""
            pub_date = item.findtext("pubDate")
            guid = item.findtext("guid") or link

            # Typical title: "Company Name: Role Title"
            company = "Unknown"
            role = title
            if ":" in title:
                company, role = [p.strip() for p in title.split(":", 1)]

            posted = None
            if pub_date:
                try:
                    posted = datetime.strptime(
                        pub_date, "%a, %d %b %Y %H:%M:%S %z"
                    )
                except ValueError:
                    posted = datetime.now(timezone.utc)

            category = _guess_category(title, description)
            external_id = f"wwr-{re.sub(r'[^a-zA-Z0-9]+', '-', guid)[:120]}"

            jobs.append(
                ScrapedJob(
                    external_id=external_id,
                    title=role or title,
                    company=company,
                    description=description,
                    apply_url=link,
                    source=self.name,
                    category=category,
                    tags=["Remote", "Full-time", category.title()],
                    posted_at=posted,
                    pakistan_friendly=True,
                )
            )
        return jobs
