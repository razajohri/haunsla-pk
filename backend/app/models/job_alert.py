from datetime import datetime, timezone

from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class JobAlert(db.Model):
    __tablename__ = "job_alerts"

    id = db.Column(db.Integer, primary_key=True)
    auth_user_id = db.Column(db.String(64), nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False)
    keyword = db.Column(db.String(255))
    category = db.Column(db.String(64))
    push_enabled = db.Column(db.Boolean, default=False)
    email_enabled = db.Column(db.Boolean, default=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "auth_user_id": self.auth_user_id,
            "email": self.email,
            "keyword": self.keyword,
            "category": self.category,
            "push_enabled": self.push_enabled,
            "email_enabled": self.email_enabled,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
