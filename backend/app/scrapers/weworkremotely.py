"""We Work Remotely RSS scraper — multiple category feeds."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from xml.etree import ElementTree

import requests

from app.scrapers.base import BaseScraper, ScrapedJob

logger = logging.getLogger(__name__)

CATEGORY_FEEDS = (
    ("tech", "https://weworkremotely.com/categories/remote-programming-jobs.rss"),
    ("tech", "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss"),
    ("design", "https://weworkremotely.com/categories/remote-design-jobs.rss"),
    ("marketing", "https://weworkremotely.com/categories/remote-marketing-jobs.rss"),
    ("writing", "https://weworkremotely.com/categories/remote-writing-jobs.rss"),
    ("support", "https://weworkremotely.com/categories/remote-customer-support-jobs.rss"),
    ("tech", "https://weworkremotely.com/categories/remote-product-jobs.rss"),
    ("finance", "https://weworkremotely.com/categories/remote-business-jobs.rss"),
    ("tech", "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss"),
    ("tech", "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss"),
    ("tech", "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss"),
)


def _guess_category(title: str, tags: str, fallback: str) -> str:
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
    return fallback


class WeWorkRemotelyScraper(BaseScraper):
    name = "weworkremotely"

    def fetch(self) -> list[ScrapedJob]:
        jobs: list[ScrapedJob] = []
        seen_urls: set[str] = set()

        for fallback_category, feed_url in CATEGORY_FEEDS:
            try:
                resp = requests.get(
                    feed_url,
                    timeout=30,
                    headers={"User-Agent": "HaunslaBot/1.0 (+https://haunsla.pk)"},
                )
                resp.raise_for_status()
                root = ElementTree.fromstring(resp.content)
            except Exception:
                logger.exception("We Work Remotely scrape failed for %s", feed_url)
                continue

            channel = root.find("channel")
            if channel is None:
                continue

            for item in channel.findall("item"):
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                if not link or link in seen_urls:
                    continue
                seen_urls.add(link)

                description = item.findtext("description") or ""
                pub_date = item.findtext("pubDate")
                guid = item.findtext("guid") or link

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

                category = _guess_category(title, description, fallback_category)
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

        logger.info("We Work Remotely: %s jobs from %s feeds", len(jobs), len(CATEGORY_FEEDS))
        return jobs
