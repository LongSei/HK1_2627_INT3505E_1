# Lab 4 — Phân tích kết quả

| Kịch bản | Users | Spawn rate | Duration | p95 (ms) | Failure rate | RPS |
|---|---:|---:|---:|---:|---:|---:|
| A | 10 | 2 | 30s | 5 | 0% (0/144) | 5.0 |
| B | 50 | 5 | 60s | 4 | 0.07% (1/1410) | 23.8 |
| C | 200 | 50 | 30s | 34 | 0.14% (4/2851) | 98.1 |

p95 theo endpoint (ms):

| Endpoint | A | B | C |
|---|---:|---:|---:|
| GET /books | 4 | 4 | 31 |
| GET /books/{id} | 5 | 3 | 34 |
| GET /books?year | 4 | 3 | 34 |
| POST /books | 31 | 5 | 45 |

1. C có p95 cao nhất (34 ms). p50 vẫn 2 ms nhưng 200 user được spawn trong 4s nên request dồn cùng lúc. Flask dev server xử lý bằng thread, bị GIL giới hạn, và SQLite khóa cả file khi ghi (POST), nên request phải xếp hàng chờ. p95 của POST ở A cao (31 ms) chỉ do mẫu nhỏ (25 request), vài lần ghi file chậm cũng đủ đẩy p95 lên.
2. Chỉ GET /books?year có failure: 0/16, 1/222, 4/439, quanh mức 1%. Đây là failure giả lập phía client (`response.failure()` trong locustfile), không phải HTTP 500 thật từ server. Tỉ lệ không tăng theo số user; số lỗi tăng chỉ vì số request tăng. 404 của GET /books/{id} là hành vi đúng (id ngẫu nhiên) nên được tính là success.
3. Cả 3 kịch bản đều đạt SLO p95 < 300 ms. RPS tăng tuyến tính (5 → 24 → 98 ≈ users / 2s chờ trung bình), nên server chưa bão hòa. Đề xuất CI gate chạy kịch bản B, fail nếu p95 > 100 ms hoặc failure thật (loại trừ lỗi giả lập) > 0%. Ngưỡng 100 ms còn dư nhiều so với số đo (4 ms) để CI không fail ngẫu nhiên.

Bonus: nếu pool giới hạn 5 kết nối (`pool_size=5, max_overflow=0`) thì 200 user đồng thời chỉ có 5 request giữ kết nối, số còn lại chờ trong hàng đợi. Latency tăng vọt; request chờ quá `pool_timeout` sẽ trả 500 (`TimeoutError`). Kiểm chứng: đặt `SQLALCHEMY_ENGINE_OPTIONS={"pool_size": 5, "max_overflow": 0, "pool_timeout": 1}`, chạy lại kịch bản C, so sánh p95/p99 và tab Failures (500 thật) với kết quả trên.

Giới hạn phép đo: Flask development server + SQLite, Locust và server chạy chung một máy, mỗi kịch bản chỉ 30–60s. Số liệu chỉ dùng để thực hành, không khẳng định được hiệu năng production.
