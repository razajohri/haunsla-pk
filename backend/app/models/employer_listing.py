from datetime import datetime, timezone

from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class EmployerListing(db.Model):
    __tablename__ = "employer_listings"

    id = db.Column(db.Integer, primary_key=True)
    employer_email = db.Column(db.String(255), nullable=False, index=True)
    company_name = db.Column(db.String(255), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"))
    placement = db.Column(db.String(32), default="standard")  # standard | featured
    price_cents = db.Column(db.Integer, default=2000)
    payment_provider = db.Column(db.String(32))  # jazzcash | easypaisa
    payment_status = db.Column(db.String(32), default="pending")
    payment_ref = db.Column(db.String(255))
    active_until = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    job = db.relationship("Job", backref=db.backref("employer_listing", uselist=False))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "employer_email": self.employer_email,
            "company_name": self.company_name,
            "job_id": self.job_id,
            "placement": self.placement,
            "price_cents": self.price_cents,
            "payment_provider": self.payment_provider,
            "payment_status": self.payment_status,
            "payment_ref": self.payment_ref,
            "active_until": self.active_until.isoformat() if self.active_until else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
