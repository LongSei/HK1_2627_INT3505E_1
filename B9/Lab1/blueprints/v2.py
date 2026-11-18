from flask import Blueprint

bp = Blueprint("v2", __name__)

USERS = {
    1: {"first_name": "Văn", "last_name": "Nguyễn", "email": "a@vnu.vn"},
    2: {"first_name": "Trang", "last_name": "Trần", "email": "b@vnu.vn"},
}


@bp.route("/users/<int:uid>")
def get_user(uid):
    u = USERS.get(uid)
    if not u:
        return {"error": "not found"}, 404
    return {
        "id": uid,
        "first_name": u["first_name"],
        "last_name": u["last_name"],
        "email": u["email"],
    }