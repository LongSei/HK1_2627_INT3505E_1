"""Bookstore API - Lab 1. Chạy: python app.py -> http://127.0.0.1:5001/api/v1/books"""
import os

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from models import Author, Book, BookAuthor, Category, Review, User, db


def create_app(db_uri="sqlite:///bookstore.db", seed_data=True):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.json.ensure_ascii = False  # trả tiếng Việt có dấu
    app.json.sort_keys = False  # giữ thứ tự field như serializer
    db.init_app(app)

    from routes.authors import bp as authors_bp
    from routes.books import bp as books_bp
    from routes.reviews import bp as reviews_bp

    app.register_blueprint(books_bp)
    app.register_blueprint(authors_bp)
    app.register_blueprint(reviews_bp)

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        # 404 route không tồn tại, 405 sai method... cũng trả JSON thay vì HTML
        if e.response is not None:  # lỗi đã có response JSON (từ get_or_404)
            return e.response
        return jsonify({"error": e.name.lower().replace(" ", "_"), "message": e.description}), e.code

    with app.app_context():
        db.drop_all()  # mỗi lần chạy bắt đầu từ dữ liệu mẫu giống nhau
        db.create_all()
        if seed_data:
            seed()
    return app


def seed():
    tech = Category(name="Công nghệ", slug="tech")
    novel = Category(name="Tiểu thuyết", slug="novel")

    martin = Author(name="Robert C. Martin", bio="Tác giả Clean Code")
    hunt = Author(name="Andrew Hunt", bio="Đồng tác giả The Pragmatic Programmer")
    thomas = Author(name="David Thomas", bio="Đồng tác giả The Pragmatic Programmer")
    kleppmann = Author(name="Martin Kleppmann", bio="Tác giả DDIA")
    nhat_anh = Author(name="Nguyễn Nhật Ánh", bio="Nhà văn")

    def book(title, isbn, price, stock, category, authors):
        b = Book(title=title, isbn=isbn, price_vnd=price, stock=stock, category=category)
        for author, role in authors:
            b.author_links.append(BookAuthor(author=author, role=role))
        return b

    clean_code = book("Clean Code", "9780132350884", 350000, 12, tech, [(martin, "lead")])
    pragmatic = book("The Pragmatic Programmer", "9780135957059", 420000, 5, tech, [(hunt, "lead"), (thomas, "co")])
    ddia = book("Designing Data-Intensive Applications", "9781449373320", 650000, 3, tech, [(kleppmann, "lead")])
    mat_biec = book("Mắt biếc", "9786042084607", 110000, 20, novel, [(nhat_anh, "lead")])
    cho_toi = book("Cho tôi xin một vé đi tuổi thơ", "9786042084614", 85000, 0, novel, [(nhat_anh, "lead")])

    an = User(email="an@example.com", display_name="An")
    binh = User(email="binh@example.com", display_name="Bình")

    db.session.add_all([tech, novel, clean_code, pragmatic, ddia, mat_biec, cho_toi, an, binh])
    db.session.add_all([
        Review(book=clean_code, user=an, rating=5),
        Review(book=clean_code, user=binh, rating=4),
        Review(book=ddia, user=an, rating=5),
        Review(book=mat_biec, user=binh, rating=3),
    ])
    db.session.commit()


if __name__ == "__main__":
    # Port 5000 trên macOS bị AirPlay chiếm nên dùng 5001
    create_app().run(host="127.0.0.1", port=int(os.environ.get("PORT", 5001)))
