# Bài 6 · CRUD in-memory cho books

| Endpoint | Status |
| -------- | ------ |
| `GET /books` | 200 |
| `GET /books/<id>` | 200 / 404 |
| `POST /books` | 201 + `Location` / 400 |
| `PUT /books/<id>` | 200 / 404 |
| `DELETE /books/<id>` | 204 / 404 |

LIST + DETAIL:

![list detail](images/01_list_detail.png)

CREATE (thiếu field → 400):

![create](images/02_create.png)

UPDATE:

![update](images/03_update.png)

DELETE:

![delete](images/04_delete.png)

![server](images/server_log.png)
