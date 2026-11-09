from flask import Blueprint
from sqlalchemy import text

from ..extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.get("/healthz")
def healthz():
    return {"status": "ok"}, 200


@health_bp.get("/ready")
def ready():
    try:
        db.session.execute(text("SELECT 1"))
        return {"status": "ready"}, 200
    except Exception:
        db.session.rollback()
        return {"status": "not_ready"}, 503
