def test_list_books_empty(client):
    r = client.get("/books")
    assert r.status_code == 200
    assert r.get_json() == []


def test_get_missing_book_404(client):
    r = client.get("/books/9999")
    assert r.status_code == 404
    assert r.get_json()["code"] == "NOT_FOUND"


def test_post_without_title_400(client):
    r = client.post("/books", json={"author": "X"})
    assert r.status_code == 400
    assert "title" in {e["field"] for e in r.get_json()["errors"]}


def test_delete_then_get_404(client):
    book_id = client.post("/books", json={"title": "DDIA", "author": "Kleppmann"}).get_json()["id"]
    assert client.delete(f"/books/{book_id}").status_code == 204
    assert client.get(f"/books/{book_id}").status_code == 404
