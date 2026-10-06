# BTVN 3: Hoàn thiện bài 6 + mở rộng
# (a) tìm kiếm GET /books?q=...
# (b) sort theo ?sort=title
# (c) bắt buộc field year là số >= 1900
from flask import Flask, jsonify, request

app = Flask(__name__)
app.json.ensure_ascii = False  # trả tiếng Việt có dấu thay vì \uXXXX

_next = 4
BOOKS = [
    {"id": 1, "title": "Clean Code", "author": "R. Martin", "year": 2008},
    {"id": 2, "title": "The Pragmatic Programmer", "author": "Hunt & Thomas", "year": 1999},
    {"id": 3, "title": "Designing Data-Intensive Applications", "author": "Kleppmann", "year": 2017},
]
SORT_FIELDS = ("id", "title", "author", "year")


def find(bid):
    return next((b for b in BOOKS if b["id"] == bid), None)


def validate_year(year):
    """Trả về thông báo lỗi, hoặc None nếu year hợp lệ."""
    # bool là con của int trong Python nên phải loại riêng
    if not isinstance(year, int) or isinstance(year, bool):
        return "year phải là số nguyên"
    if year < 1900:
        return "year phải >= 1900"
    return None


# LIST - GET /books?q=...&sort=title&limit=...
@app.route("/books", methods=["GET"])
def list_books():
    try:
        n = int(request.args.get("limit", 100))
    except ValueError:
        return {"error": "limit phải là số nguyên"}, 400

    # (a) Tìm kiếm theo title hoặc author, không phân biệt hoa thường
    q = request.args.get("q", "").strip().lower()
    items = [b for b in BOOKS if q in b["title"].lower() or q in b["author"].lower()]

    # (b) Sort: ?sort=title (tăng dần), ?sort=-title (giảm dần)
    sort = request.args.get("sort")
    if sort:
        field = sort.lstrip("-")
        if field not in SORT_FIELDS:
            return {"error": f"sort chỉ nhận {list(SORT_FIELDS)}"}, 400
        key = (lambda b: b[field].lower()) if field in ("title", "author") else (lambda b: b[field])
        items = sorted(items, key=key, reverse=sort.startswith("-"))

    return jsonify(items[:n]), 200


# DETAIL - GET /books/<id>
@app.route("/books/<int:bid>", methods=["GET"])
def get_book(bid):
    book = find(bid)
    if not book:
        return {"error": "not found"}, 404
    return jsonify(book), 200


# CREATE - POST /books
@app.route("/books", methods=["POST"])
def create_book():
    global _next
    body = request.get_json(silent=True) or {}
    t, a = body.get("title"), body.get("author")
    if not t or not a or "year" not in body:
        return {"error": "title+author+year required"}, 400

    # (c) year là số >= 1900
    err = validate_year(body["year"])
    if err:
        return {"error": err}, 400

    book = {"id": _next, "title": t, "author": a, "year": body["year"]}
    _next += 1
    BOOKS.append(book)
    return jsonify(book), 201, {"Location": f"/books/{book['id']}"}


# UPDATE - PUT, DELETE - DELETE
@app.route("/books/<int:bid>", methods=["PUT", "DELETE"])
def modify_book(bid):
    book = find(bid)
    if not book:
        return {"error": "not found"}, 404

    if request.method == "PUT":
        body = request.get_json(silent=True) or {}
        body.pop("id", None)  # không cho đổi id
        if "year" in body:
            err = validate_year(body["year"])
            if err:
                return {"error": err}, 400
        for f in ("title", "author"):
            if f in body and not body[f]:
                return {"error": f"{f} không được rỗng"}, 400
        book.update({k: v for k, v in body.items() if k in ("title", "author", "year")})
        return jsonify(book), 200

    BOOKS.remove(book)
    return "", 204


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)
