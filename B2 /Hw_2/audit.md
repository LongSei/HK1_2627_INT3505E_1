# Báo cáo Audit API: Shopify Admin REST API

* **Tài liệu tham chiếu**: [Shopify REST Admin API Reference](https://shopify.dev/docs/api/admin-rest)
---
# 5 Endpoints
## Endpoint 1: GET /products.json - Lấy danh sách sản phẩm

* **Method**: `GET`
* **Headers chính**:
* *Request*: `X-Shopify-Access-Token: {token}`, `Accept: application/json`
* *Response*: `Content-Type: application/json`, `Link: <...>; rel="next"`, `X-Shopify-Shop-Api-Call-Limit: 1/40`


* **Status Codes**:
* `200 OK`: Trả về mảng danh sách `{"products": [...]}`.
* `401 Unauthorized`: Token không hợp lệ hoặc thiếu quyền truy cập.
* `429 Too Many Requests`: Vượt ngưỡng gọi API (kèm header `Retry-After`).



---

## Endpoint 2: POST /products.json - Tạo mới sản phẩm

* **Method**: `POST` 
* **Headers chính**:
* *Request*: `Content-Type: application/json`, `X-Shopify-Access-Token: {token}`
* *Response*: `Content-Type: application/json`, `Location: .../products/{id}.json`


* **Status Codes**:
* `200 OK` / `201 Created`: Tạo thành công, trả về thông tin sản phẩm kèm ID vừa cấp.
* `400 Bad Request`: Payload JSON lỗi cú pháp.
* `422 Unprocessable Entity`: Dữ liệu vi phạm ràng buộc nghiệp vụ (thiếu trường bắt buộc, giá âm).



---

## Endpoint 3: GET /products/{id}.json - Xem chi tiết một sản phẩm

* **Method**: `GET`
* **Headers chính**:
* *Request*: `X-Shopify-Access-Token: {token}`, `If-None-Match: "..."`
* *Response*: `Content-Type: application/json`, `ETag: "..."`, `Cache-Control: private, must-revalidate`

* **Status Codes**:
* `200 OK`: Trả về đối tượng `{"product": {"id": ..., "title": ...}}`.
* `304 Not Modified`: Nội dung chưa đổi so với bản cache của client.
* `404 Not Found`: Không tìm thấy `id` tương ứng.



---

## Endpoint 4: PUT /products/{id}.json - Cập nhật sản phẩm

* **Method**: `PUT` 
* **Headers chính**:
* *Request*: `Content-Type: application/json`, `X-Shopify-Access-Token: {token}`
* *Response*: `Content-Type: application/json`


* **Status Codes**:
* `200 OK`: Cập nhật thành công, trả về representation mới của sản phẩm.
* `404 Not Found`: Không tìm thấy sản phẩm cần sửa.
* `422 Unprocessable Entity`: Dữ liệu sửa đổi không hợp lệ.



---

## Endpoint 5: DELETE /products/{id}.json - Xóa sản phẩm

* **Method**: `DELETE` 
* **Headers chính**:
* *Request*: `X-Shopify-Access-Token: {token}`
* *Response*: `Content-Type: application/json`


* **Status Codes**:
* `200 OK`: Xóa thành công, trả về body rỗng `{}`.
* `403 Forbidden`: Token không đủ quyền thực hiện xóa.
* `404 Not Found`: Sản phẩm cần xóa không tồn tại.


---

# Đánh giá tính RESTful của Shopify API

### 1. Theo 6 ràng buộc kiến trúc REST

* **Client-Server**: **Đạt** - Phân tách độc lập giao diện và dữ liệu qua HTTP/JSON.
* **Stateless**: **Đạt** - Không dùng session trên server; mỗi request mang đầy đủ thông tin xác thực qua header `X-Shopify-Access-Token`.
* **Cacheable**: **Đạt một phần** - Hỗ trợ `ETag` và `304 Not Modified`, nhưng dữ liệu quản trị chủ yếu đặt `private, no-cache`.
* **Uniform Interface**: **Đạt 3/4 ràng buộc con**:
    - **Identification of Resources**: yes
    - **Manipulation through Representation**: yes
    - **Self-descriptive messages**: yes
    - **Chưa đạt HATEOAS**: Body không chứa các link điều hướng trạng thái tiếp theo (`_links`), chỉ có header `Link` cho phân trang.

* **Layered System**: **Đạt** - Client đi qua CDN (Cloudflare) và API Gateway (xử lý auth, rate-limit 40 req/phút) trước khi tới server xử lý chính.
* **Code on Demand**: **Bỏ qua** (API không gửi code thực thi).

$\implies$ RESTFul