# =========================================================================
# 5 ENTITIES & QUAN HỆ
# =========================================================================
# | Entity   | Fields chính                | Quan hệ                 |
# | :------- | :-------------------------- | :---------------------- |
# | Book     | title, isbn, price_vnd,     | N:1 Cat; N:M Author     |
# |          | stock                       |                         |
# | Author   | name, bio                   | N:M Book                |
# | Category | name, slug                  | 1:N Book                |
# | Review   | rating, book_id, user_id    | N:1 Book; N:1 User      |
# | User     | email, display_name         | 1:N Order; 1:N Review   |
# =========================================================================
# N:M Book - Author có metadata `role` trên từng cặp -> bảng nối BookAuthor
# là một class riêng (junction resource), không dùng db.Table.
# Order nằm ngoài phạm vi Lab 1.
# =========================================================================
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import mapped_column, relationship

db = SQLAlchemy()


def utcnow():
    return datetime.now(timezone.utc)


def iso(dt):
    """ISO 8601 UTC kết thúc bằng Z. SQLite không lưu timezone nên coi giá trị là UTC."""
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Category(db.Model):
    __tablename__ = "categories"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), nullable=False)
    slug = mapped_column(String(100), unique=True, nullable=False)
    books = relationship("Book", back_populates="category")

    def to_dict(self):
        return {"id": f"cat_{self.id}", "name": self.name, "slug": self.slug}


class Author(db.Model):
    __tablename__ = "authors"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), nullable=False)
    bio = mapped_column(Text)
    book_links = relationship("BookAuthor", back_populates="author")

    def to_dict(self):
        return {"id": f"auth_{self.id}", "name": self.name, "bio": self.bio}


class BookAuthor(db.Model):
    __tablename__ = "book_authors"
    book_id = mapped_column(ForeignKey("books.id"), primary_key=True)
    author_id = mapped_column(ForeignKey("authors.id"), primary_key=True)
    role = mapped_column(String(10), nullable=False, default="co")  # lead | co | ed
    book = relationship("Book", back_populates="author_links")
    author = relationship("Author", back_populates="book_links")

    def to_dict(self):
        return {"id": f"auth_{self.author.id}", "name": self.author.name, "role": self.role}


class Book(db.Model):
    __tablename__ = "books"
    id = mapped_column(Integer, primary_key=True)
    title = mapped_column(String(200), nullable=False)
    isbn = mapped_column(String(13), unique=True)
    price_vnd = mapped_column(Integer, nullable=False)
    stock = mapped_column(Integer, nullable=False, default=0)
    category_id = mapped_column(ForeignKey("categories.id"), nullable=False)
    created_at = mapped_column(DateTime, nullable=False, default=utcnow)
    category = relationship("Category", back_populates="books")
    # Xoá sách thì xoá luôn liên kết tác giả và review (review phụ thuộc cứng vào sách)
    author_links = relationship("BookAuthor", back_populates="book", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")

    def to_dict(self):
        # Serializer = API contract: chỉ whitelist các field dưới đây
        return {
            "id": f"book_{self.id}",
            "title": self.title,
            "isbn": self.isbn,
            "price": {"amount": self.price_vnd, "currency": "VND"},
            "stock": self.stock,
            "category": self.category.to_dict(),
            "authors": [link.to_dict() for link in self.author_links],
            "createdAt": iso(self.created_at),
        }


class User(db.Model):
    __tablename__ = "users"
    id = mapped_column(Integer, primary_key=True)
    email = mapped_column(String(200), unique=True, nullable=False)
    display_name = mapped_column(String(100), nullable=False)
    reviews = relationship("Review", back_populates="user")

    def to_dict(self):
        # Không expose email ra API
        return {"id": f"u_{self.id}", "displayName": self.display_name}


class Review(db.Model):
    __tablename__ = "reviews"
    id = mapped_column(Integer, primary_key=True)
    rating = mapped_column(Integer, nullable=False)  # 1-5
    book_id = mapped_column(ForeignKey("books.id"), nullable=False)
    user_id = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at = mapped_column(DateTime, nullable=False, default=utcnow)
    book = relationship("Book", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

    def to_dict(self):
        return {
            "id": f"rev_{self.id}",
            "rating": self.rating,
            "book": {"id": f"book_{self.book.id}", "title": self.book.title},
            "user": self.user.to_dict(),
            "createdAt": iso(self.created_at),
        }
