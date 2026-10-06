# Bài 4: Path params (bắt buộc) và query string (tuỳ chọn)
from flask import Flask, jsonify, request

app = Flask(__name__)
app.json.ensure_ascii = False  # trả tiếng Việt có dấu thay vì \uXXXX

BOOKS = [
    {"id": "abc-1234", "t": "Python Crash Course", "author": "Eric Matthes"},
    {"id": "def-5678", "t": "Fluent Python", "author": "Luciano Ramalho"},
    {"id": "ghi-9012", "t": "Clean Code", "author": "Robert C. Martin"},
    {"id": "jkl-3456", "t": "Effective Python", "author": "Brett Slatkin"},
    {"id": "mno-7890", "t": "Designing Data-Intensive Applications", "author": "Martin Kleppmann"},
]


def find_by_id(book_id):
    return next((b for b in BOOKS if b["id"] == book_id), None)


# Path param: /books/<id> - id là string
@app.route("/books/<book_id>", methods=["GET"])
def get_book(book_id):
    book = find_by_id(book_id)
    if book is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(book), 200


# Ép kiểu int ngay từ URL
@app.route("/items/<int:item_id>")
def get_item(item_id):
    return jsonify({"id": item_id}), 200


# Query string: /books?limit=10&q=python
@app.route("/books", methods=["GET"])
def list_books():
    try:
        limit = int(request.args.get("limit", 20))
    except ValueError:
        return jsonify({"error": "limit phải là số nguyên"}), 400
    q = request.args.get("q", "").strip().lower()
    items = [b for b in BOOKS if q in b["t"].lower()]
    return jsonify({"items": items[:limit]}), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)
