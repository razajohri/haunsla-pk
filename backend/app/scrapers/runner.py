from __future__ import annotations

import logging

from app.extensions import db
from app.models import Job
from app.scrapers.remotive import RemotiveScraper
from app.scrapers.weworkremotely import WeWorkRemotelyScraper

logger = logging.getLogger(__name__)

SCRAPERS = [
    RemotiveScraper(),
    WeWorkRemotelyScraper(),
]


def upsert_job(data: dict) -> str:
    existing = Job.query.filter_by(external_id=data["external_id"]).first()
    if existing:
        for key, value in data.items():
            if key == "external_id":
                continue
            setattr(existing, key, value)
        return "updated"

    job = Job(**data)
    db.session.add(job)
    return "created"


def run_all_scrapers() -> dict:
    created = 0
    updated = 0
    errors: list[str] = []

    for scraper in SCRAPERS:
        try:
            scraped = scraper.fetch()
            for item in scraped:
                if not item.apply_url:
                    continue
                action = upsert_job(item.to_upsert_dict())
                if action == "created":
                    created += 1
                else:
                    updated += 1
            db.session.commit()
            logger.info("%s: processed %s jobs", scraper.name, len(scraped))
        except Exception as exc:
            db.session.rollback()
            logger.exception("Scraper %s failed", scraper.name)
            errors.append(f"{scraper.name}: {exc}")

    return {"created": created, "updated": updated, "errors": errors}
