"""
Lab 1 - Blog API: triển khai Flask routes cho collection /posts.
Version segment đặt ở URL: /api/v1
"""
import os
import random
from datetime import datetime, timedelta, timezone

from flask import Flask, Blueprint, jsonify, request, make_response, url_for

app = Flask(__name__)

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
SORTABLE_FIELDS = {"id", "title", "views", "likes", "created_at"}


def generate_posts(count=50):
    """Sinh dữ liệu mẫu cố định (seed) để kết quả chạy lại giống nhau."""
    rng = random.Random(123)
    base_time = datetime(2026, 9, 1, tzinfo=timezone.utc)
    words = ["api", "rest", "flask", "design", "cursor", "error", "http", "cache", "version", "resource"]
    posts = {}
    for i in range(1, count + 1):
        views = rng.randint(50, 100_000)
        posts[i] = {
            "id": i,
            "title": " ".join(rng.sample(words, 3)).capitalize(),
            "body": f"Nội dung bài viết số {i}",
            "author_id": rng.randint(1, 10),
            "views": views,
            "likes": rng.randint(0, views),
            "created_at": (base_time + timedelta(hours=rng.randint(0, 24 * 30))).isoformat(),
        }
    return posts


POSTS = generate_posts()
_next_id = len(POSTS) + 1

v1 = Blueprint("v1", __name__)


@v1.get("/posts")
def list_posts():
    """Danh sách bài viết: phân trang page + per_page, sort + direction."""
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", DEFAULT_PAGE_SIZE))
    except ValueError:
        return jsonify(error="page and per_page must be integers"), 400

    page = max(1, page)
    per_page = max(1, min(per_page, MAX_PAGE_SIZE))

    # --- Sort --- #
    sort_by = request.args.get("sort", "created_at")
    direction = request.args.get("direction", "desc")
    if sort_by not in SORTABLE_FIELDS:
        return jsonify(error=f"sort must be one of {sorted(SORTABLE_FIELDS)}"), 400
    if direction not in ("asc", "desc"):
        return jsonify(error="direction must be 'asc' or 'desc'"), 400

    # Thêm id làm khoá phụ để thứ tự luôn ổn định khi giá trị sort trùng nhau
    data = sorted(POSTS.values(), key=lambda p: (p[sort_by], p["id"]), reverse=(direction == "desc"))

    # --- Pagination --- #
    total = len(data)
    total_pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page  # page bắt đầu từ 1
    end = start + per_page
    data = data[start:end]

    # --- Link header (giống GitHub API) --- #
    def make_url(p):
        return url_for("v1.list_posts", page=p, per_page=per_page, sort=sort_by, direction=direction)

    links = [f'<{make_url(1)}>; rel="first"', f'<{make_url(total_pages)}>; rel="last"']
    if page > 1:
        links.append(f'<{make_url(page - 1)}>; rel="prev"')
    if page < total_pages:
        links.append(f'<{make_url(page + 1)}>; rel="next"')

    body = {
        "data": data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        },
    }
    resp = make_response(jsonify(body), 200)
    resp.headers["Link"] = ", ".join(links)
    return resp


@v1.post("/posts")
def create_post():
    """Tạo bài viết mới. Trả 201 + Location header."""
    global _next_id
    if not request.is_json:
        return jsonify(error="Content-Type must be application/json"), 415

    payload = request.get_json(silent=True) or {}
    missing = [f for f in ("title", "body", "author_id") if not payload.get(f)]
    if missing:
        return jsonify(error=f"missing fields: {missing}"), 422

    post = {
        "id": _next_id,
        "title": payload["title"],
        "body": payload["body"],
        "author_id": payload["author_id"],
        "views": 0,
        "likes": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    POSTS[_next_id] = post
    _next_id += 1

    resp = make_response(jsonify(post), 201)
    resp.headers["Location"] = url_for("v1.get_post", post_id=post["id"])
    return resp


@v1.get("/posts/<int:post_id>")
def get_post(post_id):
    post = POSTS.get(post_id)
    if post is None:
        return jsonify(error=f"post {post_id} not found"), 404
    return jsonify(post), 200


app.register_blueprint(v1, url_prefix="/api/v1")

if __name__ == "__main__":
    # Port 5000 trên macOS hay bị AirPlay chiếm nên mặc định dùng 5001
    app.run(port=int(os.environ.get("PORT", 5001)))
