"""/api/v1/reviews: top-level + filter theo user (review không cần nhiều context từ user)."""
from flask import Blueprint, request
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models import Review, db
from routes.common import error, get_or_404, parse_id

bp = Blueprint("reviews", __name__, url_prefix="/api/v1/reviews")


@bp.get("")
def list_reviews():
    q = select(Review).options(selectinload(Review.user), selectinload(Review.book)).order_by(Review.id)
    raw_user = request.args.get("user_id")
    if raw_user is not None:
        user_pk = parse_id(raw_user, "u")
        if user_pk is None:
            return error(400, "bad_request", "user_id phải có dạng u_<số>", field=["user_id"])
        q = q.where(Review.user_id == user_pk)
    return {"data": [r.to_dict() for r in db.session.scalars(q).all()]}, 200


@bp.get("/<review_id>")
def get_review(review_id):
    return get_or_404(Review, review_id, "rev", "review").to_dict(), 200
