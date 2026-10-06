# Lab 3 · Triển khai `/orders` có cursor pagination

[app.py](app.py): `GET /orders` với (1) cursor, (2) filter `status`, `customer_id`, (3) sort (`sort=total`, `sort=-total`), (4) sparse fieldsets (`fields=id,total`). `limit` mặc định 10, tối đa 100.

Cursor là base64 của `{"sort", "v", "id"}` của phần tử cuối trang (keyset); `id` làm khoá phụ khi giá trị sort trùng nhau.

## Kết quả chạy

Server:

![Server start](images/00_server_start.png)

`?status=paid`:

![Filter status](images/01_filter_status.png)

`?limit=5` rồi sang trang sau bằng `next_cursor`:

![Cursor limit](images/02_cursor_limit.png)

`?fields=id,total`:

![Sparse fields](images/03_sparse_fields.png)

`?customer_id=101`:

![Filter customer](images/04_filter_customer.png)

`?sort=-total` + cursor (hai order cùng `total = 150` vẫn đúng thứ tự theo `id`):

![Sort desc cursor](images/05_sort_desc_cursor.png)

Cursor hỏng, field không tồn tại, sort field không tồn tại → 400:

![Errors 400](images/06_errors_400.png)

Log server:

![Server log](images/07_server_log.png)
