# Lab 2 · Error handler trả về problem+json

- [errors.py](errors.py): `ProblemError` + handler cho `ProblemError`, fallback `HTTPException`, và lỗi chưa bắt (500).
- [app.py](app.py): `GET /users/<id>` raise `ProblemError` khi không tìm thấy; `/boom` cố tình gây lỗi để thử 500.

## Kết quả chạy

Server:

![Server start](images/00_server_start.png)

`/users/1` → 200; `/users/9999` → 404 `application/problem+json` có đủ `type`, `title`, `status`, `detail`, `instance`:

![User 404](images/01_user_404.png)

`Accept: application/json` hoặc không gửi `Accept` vẫn nhận problem+json:

![Accept header](images/02_accept_header.png)

Fallback `HTTPException`: route không tồn tại `/resources/42` → 404, sai method → 405 kèm header `Allow`:

![Fallback 404 405](images/03_fallback_404_405.png)

Lỗi chưa bắt → 500 với message trung tính, không lộ stack trace:

![Unhandled 500](images/04_unhandled_500.png)

Stack trace chỉ nằm ở log server (tra bằng `trace_id`):

![Server log 500](images/05_server_log_500.png)
