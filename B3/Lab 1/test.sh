#!/bin/bash
# Chạy: bash test.sh  (script tự bật server và tắt khi xong)
cd "$(dirname "$0")"
PORT="${PORT:-5001}"
BASE_URL="http://127.0.0.1:$PORT/api/v1"

PORT=$PORT python3 app.py > /dev/null 2>&1 &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null' EXIT
for _ in {1..20}; do curl -s "$BASE_URL/posts" > /dev/null && break; sleep 0.3; done

# Chỉ in id + field đang sort để dễ đọc
short() { python3 -c "import sys,json; b=json.load(sys.stdin); print('pagination:', b['pagination']); [print('  ', {k:p[k] for k in ('id',) + tuple(sys.argv[1:])}) for p in b['data']]" "$@"; }

echo "=== 1. GET /posts?page=1&per_page=3 (Mong đợi: 3 bài đầu, page=1) ==="
curl -s "$BASE_URL/posts?page=1&per_page=3" | short created_at
echo

echo "=== 2. GET /posts?page=2&per_page=3 (Mong đợi: 3 bài tiếp theo, không trùng trang 1) ==="
curl -s "$BASE_URL/posts?page=2&per_page=3" | short created_at
echo

echo "=== 3. Sort tăng dần: sort=views&direction=asc ==="
curl -s "$BASE_URL/posts?sort=views&direction=asc&per_page=5" | short views
echo

echo "=== 4. Sort giảm dần: sort=views&direction=desc ==="
curl -s "$BASE_URL/posts?sort=views&direction=desc&per_page=5" | short views
echo

echo "=== 5. per_page=1000 bị giới hạn về 100 ==="
curl -s "$BASE_URL/posts?per_page=1000" | python3 -c "import sys,json; print(json.load(sys.stdin)['pagination'])"
echo

echo "=== 6. Link header (Mong đợi: first, last, prev, next) ==="
curl -s -D - -o /dev/null "$BASE_URL/posts?page=2&per_page=10" | grep -i '^link'
echo

echo "=== 7. Sort field không tồn tại (Mong đợi: 400) ==="
curl -s -w "HTTP %{http_code}\n" "$BASE_URL/posts?sort=password"
echo

echo "=== 8. direction sai (Mong đợi: 400) ==="
curl -s -w "HTTP %{http_code}\n" "$BASE_URL/posts?sort=views&direction=up"
echo

echo "=== 9. POST /posts (Mong đợi: 201 + Location) ==="
curl -s -i -X POST "$BASE_URL/posts" -H "Content-Type: application/json" \
     -d '{"title":"Hello REST","body":"Bai viet moi","author_id":1}' | grep -iE '^(HTTP|location)|"id"'
echo

echo "=== 10. POST /posts thiếu field (Mong đợi: 422) ==="
curl -s -w "HTTP %{http_code}\n" -X POST "$BASE_URL/posts" -H "Content-Type: application/json" -d '{"title":"Thieu body"}'
echo

echo "=== 11. GET /posts/9999 (Mong đợi: 404) ==="
curl -s -w "HTTP %{http_code}\n" "$BASE_URL/posts/9999"
