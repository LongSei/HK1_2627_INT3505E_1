"""
Test cho GET /orders: tập trung vào cursor + sort.
Chạy: pytest -v
"""
import base64
import json

import pytest

import app as orders_app


@pytest.fixture
def client():
    orders_app.app.config["TESTING"] = True
    return orders_app.app.test_client()


def fetch_all(client, query="", limit=5):
    """Đi hết các trang bằng next_cursor, trả về danh sách order theo thứ tự nhận được."""
    items, cursor, pages = [], None, 0
    while True:
        url = f"/orders?limit={limit}" + (f"&{query}" if query else "") + (f"&cursor={cursor}" if cursor else "")
        resp = client.get(url)
        assert resp.status_code == 200, resp.get_json()
        body = resp.get_json()
        items.extend(body["data"])
        pages += 1
        cursor = body["pagination"]["next_cursor"]
        assert body["pagination"]["has_next"] == (cursor is not None)
        assert cursor is None or "=" not in cursor
        if cursor is None:
            return items, pages
        assert pages <= len(orders_app.ORDERS), "Vòng lặp phân trang không dừng"


def expected_order(orders, sort):
    """Tính thứ tự mong đợi độc lập với code của app: sort ổn định nhiều lượt, từ field phụ đến field chính."""
    result = sorted(orders, key=lambda o: o["id"])
    for part in reversed(sort.split(",")):
        field = part.lstrip("-")
        result = sorted(result, key=lambda o: o[field], reverse=part.startswith("-"))
    return [o["id"] for o in result]


def encode(data):
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")


# ---------------- Cursor + sort: đi hết các trang ---------------- #
SORTS = ["id", "-id", "total", "-total", "status", "-status", "customer_id",
         "status,-total", "-status,total", "customer_id,-total,status"]


@pytest.mark.parametrize("sort", SORTS)
@pytest.mark.parametrize("limit", [1, 3, 7, 50])
def test_cursor_walk_matches_sort_without_duplicates(client, sort, limit):
    items, pages = fetch_all(client, f"sort={sort}", limit)
    ids = [o["id"] for o in items]

    assert len(ids) == len(set(ids)), "Có order bị trùng giữa các trang"
    assert sorted(ids) == sorted(o["id"] for o in orders_app.ORDERS), "Có order bị sót"
    assert ids == expected_order(orders_app.ORDERS, sort)
    assert pages == -(-len(orders_app.ORDERS) // limit)


def test_ties_are_broken_by_id(client):
    """Nhiều order trùng total: trong cùng một giá trị total, id phải tăng dần, kể cả khi bị cắt giữa 2 trang."""
    items, _ = fetch_all(client, "sort=-total", limit=1)
    by_total = {}
    for o in items:
        by_total.setdefault(o["total"], []).append(o["id"])
    assert any(len(ids) > 1 for ids in by_total.values()), "Dữ liệu mẫu cần có total trùng nhau"
    for ids in by_total.values():
        assert ids == sorted(ids)


@pytest.mark.parametrize("query", ["status=paid", "customer_id=101", "status=shipped&customer_id=105"])
@pytest.mark.parametrize("sort", ["-total", "status,-total", "customer_id"])
def test_cursor_walk_with_filters(client, query, sort):
    filters = dict(p.split("=") for p in query.split("&"))
    matching = [o for o in orders_app.ORDERS
                if all(str(o[k]) == v for k, v in filters.items())]
    items, _ = fetch_all(client, f"{query}&sort={sort}", limit=2)
    assert [o["id"] for o in items] == expected_order(matching, sort)


def test_cursor_with_sparse_fields(client):
    """fields không được làm hỏng cursor dù field sort không có trong response."""
    items, _ = fetch_all(client, "sort=-total&fields=id", limit=4)
    assert all(o.keys() == {"id"} for o in items)
    assert [o["id"] for o in items] == expected_order(orders_app.ORDERS, "-total")


def test_keyset_is_stable_when_new_order_is_inserted(client, monkeypatch):
    """Ưu điểm của keyset so với offset: thêm order vào trang đã đọc không làm trang sau bị lặp."""
    monkeypatch.setattr(orders_app, "ORDERS", list(orders_app.ORDERS))
    first = client.get("/orders?sort=-total&limit=5").get_json()
    seen = [o["id"] for o in first["data"]]

    orders_app.ORDERS.append({"id": 999, "customer_id": 101, "status": "paid", "product_id": 201, "total": 10_000.0})

    second = client.get(f"/orders?sort=-total&limit=5&cursor={first['pagination']['next_cursor']}").get_json()
    assert not set(seen) & {o["id"] for o in second["data"]}
    assert 999 not in {o["id"] for o in second["data"]}


def test_link_header_points_to_next_page(client):
    resp = client.get("/orders?sort=-total&limit=5")
    cursor = resp.get_json()["pagination"]["next_cursor"]
    link = resp.headers["Link"]
    assert 'rel="next"' in link
    assert f"cursor={cursor}" in link
    assert "sort=-total" in link and "limit=5" in link

    next_url = link[link.index("<") + 1: link.index(">")]
    assert client.get(next_url).status_code == 200


def test_last_page_has_no_next(client):
    body = client.get("/orders?limit=100").get_json()
    assert body["pagination"] == {"limit": 100, "next_cursor": None, "has_next": False}


# ---------------- Cursor không hợp lệ ---------------- #
@pytest.mark.parametrize("cursor", [
    "abc!!!",                                                    # không phải base64
    base64.urlsafe_b64encode(b"not json").decode(),              # không phải JSON
    encode([1, 2, 3]),                                           # JSON nhưng không phải object
    encode({"sort": "id", "filters": {}}),                       # thiếu values
    encode({"sort": "id", "filters": {}, "values": [1, 2, 3]}),  # số giá trị không khớp sort
    encode({"sort": "id", "filters": {}, "values": ["x"]}),      # sai kiểu giá trị
])
def test_broken_cursor_returns_400_problem_json(client, cursor):
    resp = client.get(f"/orders?cursor={cursor}")
    assert resp.status_code == 400
    assert resp.mimetype == "application/problem+json"
    body = resp.get_json()
    assert {"type", "title", "status", "detail", "instance"} <= body.keys()
    assert body["status"] == 400


def test_cursor_reused_with_different_sort_returns_400(client):
    cursor = client.get("/orders?sort=-total&limit=5").get_json()["pagination"]["next_cursor"]
    resp = client.get(f"/orders?sort=total&limit=5&cursor={cursor}")
    assert resp.status_code == 400
    assert "different sort" in resp.get_json()["detail"]


def test_cursor_reused_with_different_filter_returns_400(client):
    cursor = client.get("/orders?status=paid&limit=2").get_json()["pagination"]["next_cursor"]
    resp = client.get(f"/orders?status=shipped&limit=2&cursor={cursor}")
    assert resp.status_code == 400
    assert "different filters" in resp.get_json()["detail"]


# ---------------- Sort / limit không hợp lệ ---------------- #
@pytest.mark.parametrize("sort", ["price", "-password", "total,price", "", "-", "total,-total"])
def test_invalid_sort_returns_400(client, sort):
    assert client.get(f"/orders?sort={sort}").status_code == 400


@pytest.mark.parametrize("limit,status", [("0", 400), ("-1", 400), ("abc", 400), ("1000", 200)])
def test_limit_validation(client, limit, status):
    resp = client.get(f"/orders?limit={limit}")
    assert resp.status_code == status
    if status == 200:
        assert resp.get_json()["pagination"]["limit"] == 100  # bị giới hạn trên
