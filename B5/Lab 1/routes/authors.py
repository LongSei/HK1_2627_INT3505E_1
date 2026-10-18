"""/api/v1/authors: tác giả xem danh sách sách của mình."""
from flask import Blueprint
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models import Author, Book, BookAuthor, db
from routes.common import get_or_404

bp = Blueprint("authors", __name__, url_prefix="/api/v1/authors")


@bp.get("/<author_id>")
def get_author(author_id):
    return get_or_404(Author, author_id, "auth", "author").to_dict(), 200


@bp.get("/<author_id>/books")
def list_author_books(author_id):
    author = get_or_404(Author, author_id, "auth", "author")
    books = db.session.scalars(
        select(Book)
        .join(BookAuthor, BookAuthor.book_id == Book.id)
        .where(BookAuthor.author_id == author.id)
        .options(selectinload(Book.category), selectinload(Book.author_links).selectinload(BookAuthor.author))
        .order_by(Book.id)
    ).all()
    return {"author": author.to_dict(), "data": [b.to_dict() for b in books]}, 200
