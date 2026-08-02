from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import JobAlert

bp = Blueprint("alerts", __name__)


def _require_user_id():
    return request.headers.get("X-User-Id") or request.args.get("user_id")


@bp.get("")
def list_alerts():
    user_id = _require_user_id()
    if not user_id:
        return jsonify({"error": "X-User-Id header required"}), 401

    items = JobAlert.query.filter_by(auth_user_id=user_id).all()
    return jsonify({"items": [a.to_dict() for a in items]})


@bp.post("")
def create_alert():
    user_id = _require_user_id()
    if not user_id:
        return jsonify({"error": "X-User-Id header required"}), 401

    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip()
    if not email:
        return jsonify({"error": "email is required"}), 400

    alert = JobAlert(
        auth_user_id=user_id,
        email=email,
        keyword=(payload.get("keyword") or "").strip() or None,
        category=(payload.get("category") or "").strip().lower() or None,
        push_enabled=bool(payload.get("push_enabled", False)),
        email_enabled=bool(payload.get("email_enabled", True)),
    )
    db.session.add(alert)
    db.session.commit()
    return jsonify(alert.to_dict()), 201


@bp.delete("/<int:alert_id>")
def delete_alert(alert_id: int):
    user_id = _require_user_id()
    if not user_id:
        return jsonify({"error": "X-User-Id header required"}), 401

    alert = JobAlert.query.filter_by(id=alert_id, auth_user_id=user_id).first_or_404()
    db.session.delete(alert)
    db.session.commit()
    return "", 204
