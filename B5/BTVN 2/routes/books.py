"""/api/v1/books: CRUD + sub-resource reviews (nested) + junction authors (nested + pair).
BTVN 2: GET /books có ?strategy=cursor|offset, filter ?genre, sort nhiều key ?sort=-price,title."""
from flask import Blueprint, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from models import Author, Book, BookAuthor, Category, Review, User, db
from routes.common import error, get_or_404, parse_id, validate_body
from routes.pagination import cursor_page, offset_page, order_by, parse_sort

bp = Blueprint("books", __name__, url_prefix="/api/v1/books")

DEFAULT_LIMIT = 20
MAX_LIMIT = 100

# Eager loading: lấy category + authors trong vài query cố định thay vì 1 query cho mỗi sách (N+1)
BOOK_LOAD = (
    selectinload(Book.category),
    selectinload(Book.author_links).selectinload(BookAuthor.author),
)


def find_category(raw_id):
    pk = parse_id(raw_id, "cat")
    return db.session.get(Category, pk) if pk else None


# ---------------- Collection: ?strategy=offset|cursor, ?genre, sort nhiều key (BTVN 2) ---------------- #
@bp.get("")
def list_books():
    strategy = request.args.get("strategy", "offset")
    if strategy not in ("offset", "cursor"):
        return error(400, "bad_strategy", "strategy phải là 'offset' hoặc 'cursor'")
    try:
        limit = min(int(request.args.get("limit", DEFAULT_LIMIT)), MAX_LIMIT)
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return error(400, "bad_request", "limit và offset phải là số nguyên")

    keys = parse_sort(request.args.get("sort", "id"))
    if keys is None:
        return error(400, "bad_sort", "sort chỉ nhận id, price, title, stock (thêm '-' để giảm dần)")

    q = select(Book).options(*BOOK_LOAD).order_by(*order_by(keys))
    genre = request.args.get("genre")  # thể loại = Category.slug, VD ?genre=tech
    if genre:
        q = q.join(Book.category).where(Category.slug == genre)

    if strategy == "offset":
        return offset_page(db.session, q, offset, limit), 200

    body = cursor_page(db.session, q, keys, request.args.get("cursor"), limit)
    if body is None:
        return error(400, "bad_cursor", "cursor không hợp lệ")
    return body, 200


@bp.post("")
def create_book():
    payload, err = validate_body("book-create.json")
    if err:
        return err

    category = find_category(payload["categoryId"])
    if category is None:
        return error(422, "unknown_reference", f"category {payload['categoryId']} không tồn tại", field=["categoryId"])

    # Tra hết tác giả trước, rồi mới tạo các liên kết BookAuthor
    authors = []
    for i, ref in enumerate(payload["authors"]):
        author = db.session.get(Author, parse_id(ref["id"], "auth"))
        if author is None:
            return error(422, "unknown_reference", f"author {ref['id']} không tồn tại", field=["authors", i, "id"])
        authors.append((author, ref.get("role", "co")))
    links = [BookAuthor(author=author, role=role) for author, role in authors]

    book = Book(
        title=payload["title"],
        isbn=payload.get("isbn"),
        price_vnd=payload["price"]["amount"],
        stock=payload.get("stock", 0),
        category=category,
        author_links=links,
    )
    db.session.add(book)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error(409, "conflict", f"isbn {payload.get('isbn')} đã tồn tại", field=["isbn"])
    return book.to_dict(), 201, {"Location": f"/api/v1/books/book_{book.id}"}


# ---------------- Item ---------------- #
@bp.get("/<book_id>")
def get_book(book_id):
    return get_or_404(Book, book_id, "book", "book").to_dict(), 200


@bp.patch("/<book_id>")
def update_book(book_id):
    book = get_or_404(Book, book_id, "book", "book")
    payload, err = validate_body("book-update.json")
    if err:
        return err

    if "categoryId" in payload:
        category = find_category(payload["categoryId"])
        if category is None:
            return error(422, "unknown_reference", f"category {payload['categoryId']} không tồn tại", field=["categoryId"])
        book.category = category
    if "title" in payload:
        book.title = payload["title"]
    if "isbn" in payload:
        book.isbn = payload["isbn"]
    if "price" in payload:
        book.price_vnd = payload["price"]["amount"]
    if "stock" in payload:
        book.stock = payload["stock"]

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error(409, "conflict", f"isbn {payload.get('isbn')} đã tồn tại", field=["isbn"])
    return book.to_dict(), 200


@bp.delete("/<book_id>")
def delete_book(book_id):
    book = get_or_404(Book, book_id, "book", "book")
    db.session.delete(book)  # cascade: xoá luôn book_authors và reviews của sách
    db.session.commit()
    return "", 204


# ---------------- Sub-resource: reviews (1:N, phụ thuộc cứng -> nested) ---------------- #
@bp.get("/<book_id>/reviews")
def list_book_reviews(book_id):
    book = get_or_404(Book, book_id, "book", "book")
    reviews = db.session.scalars(
        select(Review).where(Review.book_id == book.id)
        .options(selectinload(Review.user), selectinload(Review.book))
        .order_by(Review.id)
    ).all()
    return {"data": [r.to_dict() for r in reviews]}, 200


@bp.post("/<book_id>/reviews")
def create_book_review(book_id):
    book = get_or_404(Book, book_id, "book", "book")
    payload, err = validate_body("review-create.json")
    if err:
        return err
    user = db.session.get(User, parse_id(payload["userId"], "u"))
    if user is None:
        return error(422, "unknown_reference", f"user {payload['userId']} không tồn tại", field=["userId"])

    review = Review(book=book, user=user, rating=payload["rating"])
    db.session.add(review)
    db.session.commit()
    return review.to_dict(), 201, {"Location": f"/api/v1/reviews/rev_{review.id}"}


# ---------------- Junction: authors (N:M có metadata role -> nested + pair) ---------------- #
@bp.post("/<book_id>/authors")
def add_book_author(book_id):
    book = get_or_404(Book, book_id, "book", "book")
    payload, err = validate_body("book-author-create.json")
    if err:
        return err
    author = db.session.get(Author, parse_id(payload["authorId"], "auth"))
    if author is None:
        return error(422, "unknown_reference", f"author {payload['authorId']} không tồn tại", field=["authorId"])
    if db.session.get(BookAuthor, (book.id, author.id)):
        return error(409, "conflict", f"{payload['authorId']} đã là tác giả của book_{book.id}")

    link = BookAuthor(book=book, author=author, role=payload.get("role", "co"))
    db.session.add(link)
    db.session.commit()
    return {"book": {"id": f"book_{book.id}", "title": book.title}, "author": link.to_dict()}, 201
