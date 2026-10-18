"""Test Lab 2: parse_sort, cursor pagination, filter. Chạy: pytest -v"""
import pytest

from app import create_app
from models import Book, BookAuthor, Category, db
from routes.pagination import _dec, _enc, parse_sort


@pytest.fixture
def app():
    return create_app("sqlite://")


@pytest.fixture
def client(app):
    return app.test_client()


def walk(client, query, limit):
    """Đi hết các trang bằng cursor, trả về danh sách id theo thứ tự nhận được."""
    ids, cursor = [], None
    for _ in range(100):
        url = f"/api/v1/books?limit={limit}&{query}" + (f"&cursor={cursor}" if cursor else "")
        r = client.get(url)
        assert r.status_code == 200, r.get_json()
        body = r.get_json()
        ids += [b["id"] for b in body["data"]]
        cursor = body["page"]["next"]
        assert body["page"]["more"] == (cursor is not None)
        if cursor is None:
            return ids
    raise AssertionError("phân trang không dừng")


def expected(app, sort, category=None):
    """Thứ tự mong đợi, tính bằng Python thay vì SQL."""
    with app.app_context():
        books = db.session.query(Book).all()
        if category:
            books = [b for b in books if b.category.slug == category]
        key = sort.lstrip("-")
        attr = {"id": "id", "price": "price_vnd"}[key]
        books.sort(key=lambda b: (getattr(b, attr), b.id), reverse=sort.startswith("-"))
        return [f"book_{b.id}" for b in books]


# ---------------- parse_sort ---------------- #
@pytest.mark.parametrize("raw,key,desc", [("price", "price", False), ("-price", "price", True), ("id", "id", False), ("-id", "id", True)])
def test_parse_sort_valid(raw, key, desc):
    spec, err = parse_sort(raw)
    assert err is None and spec.key == key and spec.desc == desc
    assert len(spec.order_by) == 2  # luôn có id làm tie-break


@pytest.mark.parametrize("raw", ["foo", "-password", "price_vnd", "-price,title", ""])
def test_parse_sort_rejects(app, raw):
    with app.test_request_context():
        spec, err = parse_sort(raw)
        assert spec is None and err[1] == 400


def test_cursor_roundtrip_has_no_padding():
    token = _enc({"s": "-price", "f": None, "v": 350000, "i": 5})
    assert "=" not in token
    assert _dec(token) == {"s": "-price", "f": None, "v": 350000, "i": 5}


# ---------------- Cursor pagination ---------------- #
@pytest.mark.parametrize("sort", ["-id", "id", "price", "-price"])
@pytest.mark.parametrize("limit", [1, 2, 5, 100])
def test_walk_all_pages_no_duplicate_no_missing(app, client, sort, limit):
    ids = walk(client, f"sort={sort}", limit)
    assert ids == expected(app, sort)
    assert len(ids) == len(set(ids)) == 12


def test_default_sort_is_newest_first(app, client):
    assert walk(client, "", 5) == expected(app, "-id")


def test_ties_broken_by_id_across_page_boundary(client):
    """3 cuốn cùng giá 350000: limit=1 buộc ranh giới trang rơi giữa các cuốn trùng giá."""
    ids = walk(client, "sort=price", 1)
    assert ids.index("book_1") < ids.index("book_4") < ids.index("book_5")
    desc = walk(client, "sort=-price", 1)
    assert desc.index("book_5") < desc.index("book_4") < desc.index("book_1")


def test_keyset_stable_when_new_book_inserted(app, client):
    """Thêm sách mới vào đầu danh sách giữa 2 lần gọi: trang sau không bị lặp (offset sẽ bị)."""
    first = client.get("/api/v1/books?sort=-id&limit=3").get_json()
    with app.app_context():
        tech = db.session.query(Category).filter_by(slug="tech").one()
        db.session.add(Book(title="Sách mới", price_vnd=1, category=tech, author_links=[]))
        db.session.commit()
    second = client.get(f"/api/v1/books?sort=-id&limit=3&cursor={first['page']['next']}").get_json()
    seen = {b["id"] for b in first["data"]}
    assert not seen & {b["id"] for b in second["data"]}


# ---------------- Filter ---------------- #
@pytest.mark.parametrize("category", ["tech", "novel"])
def test_filter_with_cursor(app, client, category):
    ids = walk(client, f"sort=-price&category={category}", 2)
    assert ids == expected(app, "-price", category)


def test_unknown_category_returns_empty(client):
    body = client.get("/api/v1/books?category=xyz").get_json()
    assert body == {"data": [], "page": {"next": None, "more": False, "limit": 20}}


# ---------------- Lỗi ---------------- #
def test_cursor_reused_with_other_sort_is_400(client):
    cursor = client.get("/api/v1/books?sort=-price&limit=2").get_json()["page"]["next"]
    r = client.get(f"/api/v1/books?sort=price&limit=2&cursor={cursor}")
    assert r.status_code == 400 and r.get_json()["error"] == "sort_changed"


def test_cursor_reused_with_other_filter_is_400(client):
    cursor = client.get("/api/v1/books?category=tech&limit=2").get_json()["page"]["next"]
    r = client.get(f"/api/v1/books?category=novel&limit=2&cursor={cursor}")
    assert r.status_code == 400 and r.get_json()["error"] == "filter_changed"


@pytest.mark.parametrize("cursor", ["hong", _enc([1, 2]), _enc({"s": "-id", "f": None, "v": "x", "i": 1}), _enc({"s": "-id"})])
def test_broken_cursor_is_400(client, cursor):
    r = client.get(f"/api/v1/books?cursor={cursor}")
    assert r.status_code == 400 and r.get_json()["error"] == "bad_cursor"


@pytest.mark.parametrize("limit,status,effective", [("0", 200, 1), ("1000", 200, 100), ("abc", 400, None)])
def test_limit_bounds(client, limit, status, effective):
    r = client.get(f"/api/v1/books?limit={limit}")
    assert r.status_code == status
    if effective:
        assert r.get_json()["page"]["limit"] == effective
