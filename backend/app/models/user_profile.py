from datetime import datetime, timezone

from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    # Supabase auth user id (UUID string)
    auth_user_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    full_name = db.Column(db.String(255))
    skills = db.Column(db.JSON, default=list)
    experience_level = db.Column(db.String(32))
    preferred_categories = db.Column(db.JSON, default=list)
    push_token = db.Column(db.String(512))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "auth_user_id": self.auth_user_id,
            "email": self.email,
            "full_name": self.full_name,
            "skills": self.skills or [],
            "experience_level": self.experience_level,
            "preferred_categories": self.preferred_categories or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
