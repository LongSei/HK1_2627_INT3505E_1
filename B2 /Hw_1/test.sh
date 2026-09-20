#!/bin/bash

BASE_URL="http://127.0.0.1:5000"

echo "=== BÀI 1: KIỂM TRA GET & POST ==="
echo "1. GET /books (Mong đợi: Danh sách rỗng, total: 0)"
curl -s -X GET "$BASE_URL/books"
echo -e "\n"

echo "2. POST /books (Mong đợi: 201 Created)"
curl -i -s -X POST "$BASE_URL/books" \
     -H "Content-Type: application/json" \
     -d '{"title":"Clean Code", "author":"R. Martin"}'
echo -e "\n"

echo "3. POST /books thiếu field (Mong đợi: 422 Error)"
curl -i -s -X POST "$BASE_URL/books" \
     -H "Content-Type: application/json" \
     -d '{"title":"Thiếu tác giả"}'
echo -e "\n"

echo "4. POST /books thiếu Content-Type (Mong đợi: 415 Error)"
curl -i -s -X POST "$BASE_URL/books" \
     -d '{"title":"Lỗi", "author":"Header"}'
echo -e "\n"

echo "=== CHUẨN BỊ DỮ LIỆU CHO BÀI 2 & BÀI 3 ==="
curl -s -X POST "$BASE_URL/books" -H "Content-Type: application/json" -d '{"title":"Clean Architecture", "author":"R. Martin"}' > /dev/null
curl -s -X POST "$BASE_URL/books" -H "Content-Type: application/json" -d '{"title":"1984", "author":"Orwell"}' > /dev/null
curl -s -X POST "$BASE_URL/books" -H "Content-Type: application/json" -d '{"title":"Animal Farm", "author":"Orwell"}' > /dev/null
echo "Đã thêm dữ liệu mẫu giả lập."
echo -e "\n"


echo "=== BÀI 2: PUT, PATCH, DELETE ==="
echo "5. GET /books/1 (Mong đợi: Cache-Control 60s)"
curl -i -s -X GET "$BASE_URL/books/1"
echo -e "\n"

echo "6. PATCH /books/1 - Đổi 1 field (Mong đợi: 200 OK, thêm price)"
curl -i -s -X PATCH "$BASE_URL/books/1" \
     -H "Content-Type: application/json" \
     -d '{"price": 19.99}'
echo -e "\n"

echo "7. PUT /books/1 - Thay sạch toàn bộ (Mong đợi: 200 OK)"
curl -i -s -X PUT "$BASE_URL/books/1" \
     -H "Content-Type: application/json" \
     -d '{"title": "New Clean Code", "author": "Uncle Bob"}'
echo -e "\n"

echo "8. DELETE /books/1 - Xoá sách (Mong đợi: 204 No Content)"
curl -i -s -X DELETE "$BASE_URL/books/1"
echo -e "\n"


echo "=== BÀI 3: PAGINATION & FILTERING ==="
echo "9. Pagination: GET /books?page=1&size=2"
curl -s -X GET "$BASE_URL/books?page=1&size=2"
echo -e "\n\n"

echo "10. Filter by Author: GET /books?author=Orwell"
curl -s -X GET "$BASE_URL/books?author=Orwell"
echo -e "\n\n"

echo "11. Filter by Title: GET /books?q=clean"
curl -s -X GET "$BASE_URL/books?q=clean"
echo -e "\n"