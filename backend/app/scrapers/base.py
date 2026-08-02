from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ScrapedJob:
    external_id: str
    title: str
    company: str
    description: str
    apply_url: str
    source: str
    category: str | None = None
    experience_level: str | None = None
    job_type: str = "full-time"
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str = "USD"
    company_logo: str | None = None
    tags: list[str] = field(default_factory=lambda: ["Remote"])
    posted_at: datetime | None = None
    pakistan_friendly: bool = True

    def to_upsert_dict(self) -> dict[str, Any]:
        return {
            "external_id": self.external_id,
            "title": self.title,
            "company": self.company,
            "description": self.description,
            "apply_url": self.apply_url,
            "source": self.source,
            "category": self.category,
            "experience_level": self.experience_level,
            "job_type": self.job_type,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_currency": self.salary_currency,
            "company_logo": self.company_logo,
            "tags": self.tags,
            "posted_at": self.posted_at or datetime.now(timezone.utc),
            "is_remote": True,
            "pakistan_friendly": self.pakistan_friendly,
        }


class BaseScraper(ABC):
    name: str = "base"

    @abstractmethod
    def fetch(self) -> list[ScrapedJob]:
        raise NotImplementedError
