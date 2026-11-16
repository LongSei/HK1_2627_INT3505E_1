# Analysis note — Load test GET /books

Endpoint chính: `GET /books` (đọc nhiều nhất). Mỗi user chờ 1–3s giữa các request, spawn rate 50/s, mỗi mức chạy 40s.

| Users | Requests | Failures | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) | RPS |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 1004 | 0 | 2 | 13 | 44 | 48 | 25.7 |
| 200 | 3857 | 0 | 2 | 12 | 37 | 48 | 98.8 |
| 400 | 7297 | 0 | 2 | 30 | 58 | 1006 | 186.8 |
| 800 | 13038 | 0 | 3 | 32 | 54 | 143 | 333.9 |

Nhận xét:

- RPS tăng tuyến tính đến 400 user (≈ users / 2s). Ở 800 user chỉ đạt 334/400 RPS lý thuyết (83%), tức là bắt đầu bão hòa (server dev đơn tiến trình, hoặc chính Locust 1 process).
- p95 nhảy từ ~12 ms lên ~30 ms khi vượt 200 user: request bắt đầu xếp hàng.
- Ở 400 user có 1 request 1006 ms, là outlier tail. Vì vậy SLO nên đặt trên p95/p99, không dùng max.

SLO đề xuất cho `GET /books`:

- p95 < 100 ms, p99 < 250 ms, error rate < 0.1%, với tải đến 200 RPS.
- Lý do: số đo p95 cao nhất là 32 ms. Đặt ngưỡng 100 ms (khoảng 3 lần) để còn dư cho môi trường thật (mạng, DB thật, dữ liệu lớn hơn) và để CI không fail ngẫu nhiên. 200 RPS là mức đã đo được ổn định và chưa bão hòa.
- CI gate: chạy mức 200 user trong 40s, fail nếu p95 > 100 ms hoặc failure > 0.1%.

Giới hạn: Flask dev server + SQLite, Locust và server chạy chung một máy. SLO production cần đo lại trên môi trường giống production.
