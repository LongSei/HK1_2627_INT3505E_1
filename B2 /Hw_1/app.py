"""
Main Application Module cho Hệ thống Sách và Đơn hàng.
Cung cấp các API RESTful quản lý tài nguyên.
"""
from flask import Flask, jsonify, request, make_response
from books import SQLiteBookRepository
from orders import SQLiteOrderRepository
from database import SqliteDatabaseManager

app = Flask(__name__)

DATABASE = "books.db"
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

db_manager = SqliteDatabaseManager(DATABASE)
book_repo = SQLiteBookRepository(db_manager)
order_repo = SQLiteOrderRepository(db_manager)

@app.get("/books")
def list_books():
    """Lấy danh sách sách có phân trang và bộ lọc. Logic xử lý toàn bộ trên RAM."""
    try: 
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", DEFAULT_PAGE_SIZE))
    except ValueError:
        return jsonify(error="page and size must be integers"), 400
    
    page = max(1, page)
    size = max(1, min(size, MAX_PAGE_SIZE))

    # Kéo toàn bộ dữ liệu từ DB lên
    ALL_BOOKS = book_repo.get_books()

    # --- Filtering --- #
    flt = ALL_BOOKS 
    a = (request.args.get("author") or "").strip()
    if a: 
        flt = [b for b in flt if a.lower() in b["author"].lower()]
    q = (request.args.get("q") or "").strip()
    if q: 
        flt = [b for b in flt if q.lower() in b["title"].lower()]

    # --- Pagination --- #
    total = len(flt) 
    start = (page - 1) * size 
    end = start + size 
    data = flt[start:end] 
    last = (total + size - 1) // size if total > 0 else 1

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
    resp.headers["Cache-Control"] = "public, max-age=30" 
    return resp


@app.get("/books/<int:bid>")
def fetch(bid): 
    """Truy xuất một cuốn sách theo ID bằng cách duyệt danh sách tại tầng App."""
    ALL_BOOKS = book_repo.get_books()
    book = next(
        (b for b in ALL_BOOKS if b["id"] == bid), 
        None
    )
    if book is None: 
        return jsonify(error="not found"), 404
        
    resp = make_response(jsonify(book), 200)
    resp.headers["Cache-Control"] = "max-age=60" 
    return resp


@app.put("/books/<int:bid>")
def put(bid): 
    """Ghi đè thông tin sách. Kiểm tra tồn tại bằng cách duyệt mảng tại tầng App."""
    ALL_BOOKS = book_repo.get_books()
    book_exists = any(b["id"] == bid for b in ALL_BOOKS)
    
    if not book_exists: 
        return jsonify(error="not found"), 404

    p = request.get_json(silent=True) or {}
    t = (p.get("title") or "").strip()
    a = (p.get("author") or "").strip()

    if not t or not a:
        return jsonify(error="Title and Author required"), 422

    # Yêu cầu DB thực thi ghi nhận
    book_repo.update_book(bid, title=t, author=a, isbn=p.get("isbn", ""), price=p.get("price", 0.0))
    
    # Kéo mảng mới nhất lên để lấy response
    updated_book = next((b for b in book_repo.get_books() if b["id"] == bid), None)
    return jsonify(updated_book), 200


@app.patch("/books/<int:bid>")
def patch(bid): 
    """Cập nhật một phần thông tin sách. Kiểm tra tồn tại qua mảng."""
    ALL_BOOKS = book_repo.get_books()
    book_exists = any(b["id"] == bid for b in ALL_BOOKS)
    
    if not book_exists: 
        return jsonify(error="not found"), 404

    p = request.get_json(silent=True) or {}
    if "price" in p and p.get("price", 0) < 0: 
        return jsonify(error="Price must be >= 0"), 422
    
    allowed_fields = ("title", "author", "isbn", "price")
    update_data = {k: v for k, v in p.items() if k in allowed_fields}
    
    if not update_data:
        return jsonify(error="No valid fields to update"), 400

    book_repo.patch_book(bid, update_fields=update_data)

    updated_book = next((b for b in book_repo.get_books() if b["id"] == bid), None)
    return jsonify(updated_book), 200


@app.delete("/books/<int:bid>")
def delete(bid): 
    """Xóa sách theo ID. Kiểm tra tồn tại tại tầng App trước khi xóa."""
    ALL_BOOKS = book_repo.get_books()
    book_exists = any(b["id"] == bid for b in ALL_BOOKS)
    
    if not book_exists: 
        return jsonify(error="not found"), 404

    book_repo.delete_book(bid)
    return "", 204


@app.post("/books")
def create_book(): 
    """Tạo mới sách và lưu xuống CSDL."""
    if not request.is_json: 
        return jsonify(error="Expected JSON"), 415

    p = request.get_json(silent=True) or {}
    t = (p.get("title") or "").strip()
    a = (p.get("author") or "").strip() 

    if not t or not a: 
        return jsonify(error="Title and Author required"), 422 

    new_id = book_repo.create_book(title=t, author=a, isbn=p.get("isbn", ""), price=p.get("price", 0.0))
    
    # Duyệt mảng để trả về object hoàn chỉnh theo Location mới tạo
    created_book = next((b for b in book_repo.get_books() if b["id"] == new_id), None)

    resp = make_response(jsonify(created_book), 201)
    resp.headers["Location"] = f"/books/{new_id}"
    return resp


@app.get("/orders/<int:oid>")
def fetch_order(oid):
    """Lấy thông tin đơn hàng theo ID. Logic kiểm tra có thể thực hiện thông qua Repo."""
    order = order_repo.get_order_by_id(oid)
    if not order:
        return jsonify(error="order not found"), 404
        
    return jsonify(order), 200