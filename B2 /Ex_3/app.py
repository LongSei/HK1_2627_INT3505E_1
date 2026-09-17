from flask import Flask, jsonify, request, make_response

app = Flask(__name__)

BOOKS = [
    {"id": 1, "title": "Machine Learning Learning", "author": "Andrew Ng", "isbn": "978-0999736403", "price": 0},
    {"id": 2, "title": "Deep Learning", "author": "Ian Goodfellow", "isbn": "978-0262035613", "price": 0},
    {"id": 3, "title": "Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow", "author": "Aurélien Géron", "isbn": "978-1492032649", "price": 0}
]
_next_id = 4
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

@app.get("/books")
def list_books():
    try: 
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", DEFAULT_PAGE_SIZE))
    except ValueError:
        return jsonify(error="page and size must be integers"), 400
    
    page = max(1, page)
    size = max(1, min(size, MAX_PAGE_SIZE))

    # --- Filtering --- #
    flt = BOOKS 
    a = (request.args.get("author") or "").strip()
    if a: 
        flt = [b for b in flt if a.lower() in b["author"].lower()]
    q = (request.args.get("q") or "").strip()
    if q: 
        flt = [b for b in flt if q.lower() in b["title"].lower()]

    # --- Pagination --- #
    total = len(flt) # tổng số sách sau khi lọc
    start = (page - 1) * size # chỉ số của phần tử đầu tiên trong trang hiện tại
    end = start + size # chỉ số của phần tử cuối cùng trong trang hiện tại
    data = flt[start:end] # lấy ra các sách trong trang hiện tại
    last = (total + size - 1) // size # tính số trang cuối cùng

    # --- HATEOAS --- #
    def make_url(p): 
        return f"/books?page={p}&size={size}" 
    links = {
        "self": {"href": make_url(page)},
        "first": {"href": make_url(1)},
        "last": {"href": make_url(max(1, last))}
    }
    if page > 1: 
        links["prev"] = {"href": make_url(page - 1)}
    if end < total: 
        links["next"] = {"href": make_url(page + 1)}
    body = {
        "data": data,
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "last": last
        },
        "_links": links
    }
    resp = make_response(jsonify(body), 200)
    resp.headers["Cache-Control"] = "public, max-age=30" # 30s cache + public
    return resp

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