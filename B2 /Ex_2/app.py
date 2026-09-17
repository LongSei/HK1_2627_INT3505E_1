from flask import Flask, jsonify, request, make_response
app = Flask(__name__)
BOOKS = [

]
_next_id = 1
# --- GET /books --- trả danh sách
@app.get("/books")
def list_books(): 
    return jsonify({
        "data": BOOKS, 
        "total": len(BOOKS)
    }), 200

# --- GET /books/<int:bid> --- lấy thông tin sách theo ID
@app.get("/books/<int:bid>")
def fetch(bid): 
    i = next(
        (k for k, b in enumerate(BOOKS) if b["id"] == bid), 
        None
    )
    if i is None: 
        return jsonify(error="not found"), 404
    resp = make_response(jsonify(BOOKS[i]), 200)
    resp.headers["Cache-Control"] = "max-age=60" # 60s cache
    return resp

# --- PUT /books/<int:bid> --- cập nhật thông tin sách theo ID 
@app.put("/books/<int:bid>")
def put(bid): 
    i = next(
        (k for k, b in enumerate(BOOKS) if b["id"] == bid), 
        None
    )
    if i is None: 
        return jsonify(error="not found"), 404

    p = request.get_json(silent=True) or {}
    t = (p.get("title") or "").strip()
    a = (p.get("author") or "").strip()

    if not t or not a:
        return jsonify(error="Title and Author required"), 422

    BOOKS[i] = {
        "id": bid,
        "title": t,
        "author": a, 
        "isbn": p.get("isbn") or "",
        "price": p.get("price") or None
    }

    return jsonify(BOOKS[i]), 200

# --- Patch /books/<int:bid> --- cập nhật thông tin sách theo ID (chỉ những trường được cung cấp)
@app.patch("/books/<int:bid>")
def patch(bid): 
    i = next(
        (k for k, b in enumerate(BOOKS) if b["id"] == bid), 
        None
    )
    if i is None: 
        return jsonify(error="not found"), 404

    p = request.get_json(silent=True) or {}
    if p.get("price", 0) < 0: 
        return jsonify(error="Price must be >= 0"), 422
    
    for k in ("title", "author", "isbn", "price"): 
        if k in p: 
            BOOKS[i][k] = p[k]

    return jsonify(BOOKS[i]), 200

# --- DELETE /books/<int:bid> --- xóa sách theo ID 
@app.delete("/books/<int:bid>")
def delete(bid): 
    i = next(
        (k for k, b in enumerate(BOOKS) if b["id"] == bid), 
        None
    )
    if i is None: 
        return jsonify(error="not found"), 404

    BOOKS.pop(i)
    return "", 204

# --- POST /books --- tạo mới
@app.post("/books")
def create_book(): 
    global _next_id 
    if not request.is_json: 
        return jsonify(error="Expected JSON"), 415

    p = request.get_json(silent=True) or {}
    t = (p.get("title") or "").strip()
    a = (p.get("author") or "").strip() 

    if not t or not a: 
        return jsonify(error="Title and Author required"), 422 

    book = {
        "id": _next_id, 
        "title": t, 
        "author": a
    }

    BOOKS.append(book)
    _next_id += 1
    resp = make_response(jsonify(book), 201)
    resp.headers["Location"] = f"/books/{book['id']}"
    return resp