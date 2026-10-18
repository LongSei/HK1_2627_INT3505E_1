"""Đếm số câu SQL khi serialize danh sách sách: lazy loading (N+1) vs eager loading (selectinload)."""
from sqlalchemy import event, select

from app import create_app
from models import Book, db
from routes.books import BOOK_LOAD

app = create_app("sqlite://")

with app.app_context():
    statements = []
    event.listen(db.engine, "before_cursor_execute", lambda *args: statements.append(args[2]))

    def count(label, query):
        db.session.expunge_all()  # xoá cache của session để mỗi lần đo đều đọc lại từ DB
        statements.clear()
        books = db.session.scalars(query).all()
        [b.to_dict() for b in books]
        print(f"{label:<28} {len(books)} sách -> {len(statements)} câu SQL")

    count("Lazy (không eager load)", select(Book))
    count("Eager (selectinload)", select(Book).options(*BOOK_LOAD))
