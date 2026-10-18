"""Test GET /api/v1/books: offset, cursor, genre, sort nhiều key. Chạy: pytest -v"""
import pytest

from app import create_app


@pytest.fixture
def client():
    return create_app("sqlite://").test_client()


def get(client, query):
    r = client.get(f"/api/v1/books?{query}")
    assert r.status_code == 200, r.get_json()
    return r.get_json()


def all_pages_cursor(client, query, limit=3):
    ids, cursor = [], ""
    while True:
        body = get(client, f"strategy=cursor&limit={limit}&{query}&cursor={cursor}")
        ids += [b["id"] for b in body["data"]]
        cursor = body["page"]["next"]
        if not cursor:
            return ids


def all_pages_offset(client, query, limit=3):
    ids, offset = [], 0
    while True:
        body = get(client, f"strategy=offset&limit={limit}&offset={offset}&{query}")
        ids += [b["id"] for b in body["data"]]
        offset += limit
        if offset >= body["page"]["total"]:
            return ids


def test_offset_returns_total(client):
    body = get(client, "strategy=offset&limit=5&offset=0")
    assert len(body["data"]) == 5
    assert body["page"] == {"strategy": "offset", "offset": 0, "limit": 5, "total": 12}


def test_offset_second_page(client):
    body = get(client, "strategy=offset&limit=5&offset=5")
    assert [b["id"] for b in body["data"]] == ["book_6", "book_7", "book_8", "book_9", "book_10"]


def test_cursor_walk_all_books(client):
    ids = all_pages_cursor(client, "sort=id")
    assert ids == [f"book_{i}" for i in range(1, 13)]


def test_cursor_and_offset_same_order(client):
    assert all_pages_cursor(client, "sort=-price,title") == all_pages_offset(client, "sort=-price,title")


def test_multi_key_sort(client):
    books = get(client, "sort=-price,title&limit=100")["data"]
    pairs = [(b["price"]["amount"], b["title"]) for b in books]
    assert pairs == sorted(pairs, key=lambda p: (-p[0], p[1]))


@pytest.mark.parametrize("strategy", ["offset", "cursor"])
def test_genre_filter(client, strategy):
    books = get(client, f"strategy={strategy}&genre=novel&limit=100")["data"]
    assert len(books) == 6
    assert all(b["category"]["slug"] == "novel" for b in books)


def test_genre_with_cursor_multi_key(client):
    ids = all_pages_cursor(client, "genre=novel&sort=price,-title", limit=2)
    assert len(ids) == len(set(ids)) == 6


@pytest.mark.parametrize("query", ["sort=foo", "strategy=page", "limit=abc", "strategy=cursor&cursor=hong"])
def test_bad_params_return_400(client, query):
    assert client.get(f"/api/v1/books?{query}").status_code == 400
