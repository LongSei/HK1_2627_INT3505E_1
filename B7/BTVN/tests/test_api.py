import pytest
from sqlalchemy import event

from app import create_app
from app.extensions import db


@pytest.fixture
def client():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite://", "TESTING": True})
    with app.app_context():
        yield app.test_client()


def create_product(client, sku, price=1000):
    return client.post("/api/v1/products", json={"sku": sku, "name": sku, "price_cents": price})


def count_queries(fn):
    queries = []
    listener = lambda *args: queries.append(args[2])
    event.listen(db.engine, "before_cursor_execute", listener)
    try:
        response = fn()
    finally:
        event.remove(db.engine, "before_cursor_execute", listener)
    return response, len(queries)


def test_post_product(client):
    r = create_product(client, "BK-001", 350000)
    assert r.status_code == 201
    assert r.get_json()["qty_in_stock"] == 0
    assert create_product(client, "BK-001").status_code == 409
    assert client.post("/api/v1/products", json={"sku": "a"}).status_code == 422


def test_get_order_uses_eager_loading(client):
    for i in range(10):
        create_product(client, f"SKU-{i}")
    small = client.post("/api/v1/orders", json={"items": [{"product_id": 1, "qty": 1}]}).get_json()["id"]
    big = client.post("/api/v1/orders", json={"items": [{"product_id": i, "qty": 1} for i in range(1, 11)]}).get_json()["id"]

    r1, q1 = count_queries(lambda: client.get(f"/api/v1/orders/{small}"))
    r10, q10 = count_queries(lambda: client.get(f"/api/v1/orders/{big}"))

    assert r1.status_code == r10.status_code == 200
    assert len(r10.get_json()["items"]) == 10
    assert q1 == q10
