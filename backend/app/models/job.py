from datetime import datetime, timezone

from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(255), unique=True, index=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    company = db.Column(db.String(255), nullable=False, index=True)
    company_logo = db.Column(db.String(512))
    description = db.Column(db.Text, nullable=False, default="")
    apply_url = db.Column(db.String(1024), nullable=False)
    category = db.Column(db.String(64), index=True)  # tech, design, marketing...
    experience_level = db.Column(db.String(32), index=True)  # entry, mid, senior
    job_type = db.Column(db.String(32), index=True)  # full-time, part-time...
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    salary_currency = db.Column(db.String(8), default="USD")
    tags = db.Column(db.JSON, default=list)
    source = db.Column(db.String(64), index=True)
    is_remote = db.Column(db.Boolean, default=True, index=True)
    pakistan_friendly = db.Column(db.Boolean, default=True, index=True)
    haunsla_score = db.Column(db.Integer)  # post-MVP
    is_featured = db.Column(db.Boolean, default=False, index=True)
    posted_at = db.Column(db.DateTime(timezone=True), default=utcnow, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    def to_dict(self, include_description: bool = False) -> dict:
        data = {
            "id": self.id,
            "external_id": self.external_id,
            "title": self.title,
            "company": self.company,
            "company_logo": self.company_logo,
            "apply_url": self.apply_url,
            "category": self.category,
            "experience_level": self.experience_level,
            "job_type": self.job_type,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_currency": self.salary_currency,
            "tags": self.tags or [],
            "source": self.source,
            "is_remote": self.is_remote,
            "pakistan_friendly": self.pakistan_friendly,
            "haunsla_score": self.haunsla_score,
            "is_featured": self.is_featured,
            "posted_at": self.posted_at.isoformat() if self.posted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_description:
            data["description"] = self.description
        return data
