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