from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import EmployerListing, Job

bp = Blueprint("employers", __name__)

PLACEMENT_PRICES = {
    "standard": 2000,  # $20 in cents
    "featured": 5000,  # $50 in cents
}


@bp.post("/listings")
def create_listing():
    """Create an employer job listing (payment integration stub)."""
    payload = request.get_json(silent=True) or {}
    required = ["employer_email", "company_name", "title", "description", "apply_url"]
    missing = [f for f in required if not payload.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    placement = (payload.get("placement") or "standard").lower()
    if placement not in PLACEMENT_PRICES:
        return jsonify({"error": "placement must be standard or featured"}), 400

    job = Job(
        external_id=f"employer-{payload['employer_email']}-{datetime.now(timezone.utc).timestamp()}",
        title=payload["title"].strip(),
        company=payload["company_name"].strip(),
        company_logo=payload.get("company_logo"),
        description=payload["description"].strip(),
        apply_url=payload["apply_url"].strip(),
        category=(payload.get("category") or "tech").lower(),
        experience_level=(payload.get("experience_level") or "mid").lower(),
        job_type=(payload.get("job_type") or "full-time").lower(),
        salary_min=payload.get("salary_min"),
        salary_max=payload.get("salary_max"),
        salary_currency=payload.get("salary_currency", "USD"),
        tags=payload.get("tags") or ["Remote", "Employer"],
        source="employer",
        is_remote=True,
        pakistan_friendly=True,
        is_featured=placement == "featured",
        posted_at=datetime.now(timezone.utc),
    )
    db.session.add(job)
    db.session.flush()

    listing = EmployerListing(
        employer_email=payload["employer_email"].strip(),
        company_name=payload["company_name"].strip(),
        job_id=job.id,
        placement=placement,
        price_cents=PLACEMENT_PRICES[placement],
        payment_provider=payload.get("payment_provider"),  # jazzcash | easypaisa
        payment_status="pending",
        active_until=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.session.add(listing)
    db.session.commit()

    return (
        jsonify(
            {
                "listing": listing.to_dict(),
                "job": job.to_dict(include_description=True),
                "checkout": {
                    "amount_cents": listing.price_cents,
                    "currency": "USD",
                    "providers": ["jazzcash", "easypaisa"],
                    "note": "Payment gateway integration coming in Week 4",
                },
            }
        ),
        201,
    )


@bp.get("/listings")
def list_employer_listings():
    email = request.args.get("email", "").strip()
    if not email:
        return jsonify({"error": "email query param required"}), 400
    items = (
        EmployerListing.query.filter_by(employer_email=email)
        .order_by(EmployerListing.created_at.desc())
        .all()
    )
    return jsonify({"items": [i.to_dict() for i in items]})
