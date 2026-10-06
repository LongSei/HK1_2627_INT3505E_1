#!/bin/bash
# Chạy: bash test.sh  (script tự bật server và tắt khi xong)
cd "$(dirname "$0")"
PORT="${PORT:-5001}"
BASE_URL="http://127.0.0.1:$PORT"

PORT=$PORT python3 app.py > server.log 2>&1 &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null' EXIT
for _ in {1..20}; do curl -s "$BASE_URL/users/1" > /dev/null && break; sleep 0.3; done

echo "=== 1. GET /users/1 (Mong đợi: 200) ==="
curl -s -i "$BASE_URL/users/1" | grep -vE '^(Server|Date|Connection|Content-Length):'
echo -e "\n"

echo "=== 2. GET /users/9999 (Mong đợi: 404 + application/problem+json) ==="
curl -s -i "$BASE_URL/users/9999" | grep -vE '^(Server|Date|Connection|Content-Length):'
echo -e "\n"

echo "=== 3. Accept: application/json vẫn nhận problem+json ==="
curl -s -i -H "Accept: application/json" "$BASE_URL/users/9999" | grep -iE '^(HTTP|Content-Type)'
echo

echo "=== 4. Không gửi Accept vẫn nhận problem+json ==="
curl -s -i -H "Accept:" "$BASE_URL/users/9999" | grep -iE '^(HTTP|Content-Type)'
echo

echo "=== 5. Route không tồn tại /resources/42 (Mong đợi: 404 qua handler fallback HTTPException) ==="
curl -s -i "$BASE_URL/resources/42" | grep -vE '^(Server|Date|Connection|Content-Length):'
echo -e "\n"

echo "=== 6. Sai method DELETE /users/1 (Mong đợi: 405 problem+json) ==="
curl -s -i -X DELETE "$BASE_URL/users/1" | grep -vE '^(Server|Date|Connection|Content-Length):'
echo -e "\n"

echo "=== 7. Lỗi chưa bắt /boom (Mong đợi: 500, message trung tính, không có stack trace) ==="
curl -s -i "$BASE_URL/boom" | grep -vE '^(Server|Date|Connection|Content-Length):'
echo -e "\n"

sleep 0.3
echo "=== 8. Log phía server cho lỗi 500 (chi tiết chỉ nằm ở server) ==="
grep -A3 "Unhandled error" server.log | head -4
echo "..."
grep "ZeroDivisionError" server.log
