from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import Job, SavedJob

bp = Blueprint("saved", __name__)


def _require_user_id():
    user_id = request.headers.get("X-User-Id") or request.args.get("user_id")
    if not user_id:
        return None
    return user_id


@bp.get("")
def list_saved():
    user_id = _require_user_id()
    if not user_id:
        return jsonify({"error": "X-User-Id header required"}), 401

    items = (
        SavedJob.query.filter_by(auth_user_id=user_id)
        .order_by(SavedJob.created_at.desc())
        .all()
    )
    return jsonify({"items": [item.to_dict() for item in items]})


@bp.post("")
def save_job():
    user_id = _require_user_id()
    if not user_id:
        return jsonify({"error": "X-User-Id header required"}), 401

    payload = request.get_json(silent=True) or {}
    job_id = payload.get("job_id")
    if not job_id:
        return jsonify({"error": "job_id is required"}), 400

    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    existing = SavedJob.query.filter_by(auth_user_id=user_id, job_id=job_id).first()
    if existing:
        return jsonify(existing.to_dict())

    saved = SavedJob(auth_user_id=user_id, job_id=job_id)
    db.session.add(saved)
    db.session.commit()
    return jsonify(saved.to_dict()), 201


@bp.patch("/<int:saved_id>")
def update_saved(saved_id: int):
    user_id = _require_user_id()
    if not user_id:
        return jsonify({"error": "X-User-Id header required"}), 401

    saved = SavedJob.query.filter_by(id=saved_id, auth_user_id=user_id).first_or_404()
    payload = request.get_json(silent=True) or {}
    if "applied" in payload:
        saved.applied = bool(payload["applied"])
    db.session.commit()
    return jsonify(saved.to_dict())


@bp.delete("/<int:saved_id>")
def delete_saved(saved_id: int):
    user_id = _require_user_id()
    if not user_id:
        return jsonify({"error": "X-User-Id header required"}), 401

    saved = SavedJob.query.filter_by(id=saved_id, auth_user_id=user_id).first_or_404()
    db.session.delete(saved)
    db.session.commit()
    return "", 204
