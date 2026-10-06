# Bài 4 · Path params và query string

- Path param: `GET /books/<book_id>` (không có → 404), `GET /items/<int:item_id>` (không phải số → 404)
- Query string: `GET /books?limit=5&q=python`

![curl](images/01_path_query.png)

![server](images/server_log.png)
