from datetime import datetime, timezone

from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class SavedJob(db.Model):
    __tablename__ = "saved_jobs"
    __table_args__ = (
        db.UniqueConstraint("auth_user_id", "job_id", name="uq_user_job"),
    )

    id = db.Column(db.Integer, primary_key=True)
    auth_user_id = db.Column(db.String(64), nullable=False, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    applied = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    job = db.relationship("Job", backref=db.backref("saves", lazy="dynamic"))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "auth_user_id": self.auth_user_id,
            "job_id": self.job_id,
            "applied": self.applied,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "job": self.job.to_dict() if self.job else None,
        }
