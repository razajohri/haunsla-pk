from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    return jsonify({"status": "ok", "service": "haunsla-api", "version": "0.1.0"})


@bp.get("/")
def root():
    return jsonify(
        {
            "name": "Haunsla API",
            "tagline": "Remote Jobs. Real Ambition.",
            "docs": "/api/jobs",
        }
    )
