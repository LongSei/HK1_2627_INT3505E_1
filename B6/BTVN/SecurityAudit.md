# Security Audit · Social Network API

Các điểm có thể lộ ở 3 endpoint `POST /auth/login`, `POST /auth/refresh`, `GET /posts/{id}`.

| # | Điểm có thể lộ | Endpoint | Rủi ro | Cách chặn | OWASP API 2023 |
| - | -------------- | -------- | ------ | --------- | -------------- |
| 1 | Thông báo lỗi login khác nhau giữa "sai email" và "sai mật khẩu" | login | Dò được email nào đã đăng ký | Luôn trả `401 invalid_credentials` cho cả hai trường hợp | API2 Broken Authentication |
| 2 | Không giới hạn số lần đăng nhập | login | Brute force, credential stuffing | Sai 5 lần/phút → `429` + `Retry-After` | API2, API4 Unrestricted Resource Consumption |
| 3 | Chỉ kiểm token, không kiểm quyền trên từng bài viết | `GET /posts/{id}` | User A đổi `{id}` để đọc bài private của B (BOLA) | Kiểm `visibility` và chủ bài; bài private của người khác trả `404` (không trả 403 để không lộ bài có tồn tại) | API1 BOLA |
| 4 | Refresh token dùng lại được nhiều lần | refresh | Token bị đánh cắp dùng mãi trong 30 ngày | Rotation: mỗi refresh token chỉ dùng 1 lần, `jti` cũ bị thu hồi; dùng lại → `401` | API2 |
| 5 | Dùng nhầm loại token / không kiểm chữ ký, `exp` | cả 3 | Giả mạo token, dùng token hết hạn, dùng refresh token để gọi API | Thư viện kiểm chữ ký + `exp`; access token 15 phút; kiểm `type` của token (refresh không gọi được `/posts`, access không refresh được) | API2 |
| 6 | Secret JWT hoặc mật khẩu lưu sai cách | cả 3 | Lộ secret (VD commit lên Git) là giả được mọi token; lộ DB là lộ mật khẩu | Secret đọc từ biến môi trường `JWT_SECRET_KEY`; mật khẩu chỉ lưu dạng hash (Werkzeug scrypt), không lưu plain/MD5 | API8 Security Misconfiguration |

Chưa xử lý trong bản demo (cần khi lên production): chạy qua HTTPS, lưu danh sách token thu hồi trong Redis/DB thay vì bộ nhớ, rate limit theo cả tài khoản lẫn IP.
