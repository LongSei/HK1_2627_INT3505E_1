#!/bin/bash
# Chạy: bash test.sh  (script tự bật server và tắt khi xong)
cd "$(dirname "$0")"
PORT="${PORT:-5001}"
BASE_URL="http://127.0.0.1:$PORT"

PORT=$PORT python3 app.py > /dev/null 2>&1 &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null' EXIT
for _ in {1..20}; do curl -s "$BASE_URL/orders" > /dev/null && break; sleep 0.3; done

next_cursor() { python3 -c "import sys,json; print(json.load(sys.stdin)['pagination']['next_cursor'])"; }

echo "=== 1. curl '$BASE_URL/orders?status=paid' (Mong đợi: chỉ order status=paid) ==="
curl -s "$BASE_URL/orders?status=paid" | python3 -m json.tool
echo

echo "=== 2. curl '$BASE_URL/orders?limit=5' (Mong đợi: 5 order + next_cursor) ==="
PAGE1=$(curl -s "$BASE_URL/orders?limit=5")
echo "$PAGE1" | python3 -m json.tool
CURSOR=$(echo "$PAGE1" | next_cursor)
echo

echo "=== 2b. Trang tiếp theo bằng next_cursor (Mong đợi: id 6..10) ==="
curl -s "$BASE_URL/orders?limit=5&cursor=$CURSOR" | python3 -m json.tool
echo

echo "=== 3. curl '$BASE_URL/orders?fields=id,total' (Mong đợi: chỉ có id, total) ==="
curl -s "$BASE_URL/orders?fields=id,total&limit=4" | python3 -m json.tool
echo

echo "=== 4. Filter customer_id=101 ==="
curl -s "$BASE_URL/orders?customer_id=101&fields=id,customer_id,total" | python3 -m json.tool
echo

echo "=== 5. Sort giảm dần theo total + cursor: sort=-total&limit=3, rồi trang tiếp ==="
PAGE1=$(curl -s "$BASE_URL/orders?sort=-total&limit=3&fields=id,total")
echo "$PAGE1" | python3 -m json.tool
CURSOR=$(echo "$PAGE1" | next_cursor)
curl -s "$BASE_URL/orders?sort=-total&limit=3&fields=id,total&cursor=$CURSOR" | python3 -m json.tool
echo

echo "=== 6. Cursor hỏng (Mong đợi: 400) ==="
curl -s -i "$BASE_URL/orders?cursor=abc!!!" | grep -iE '^(HTTP|Content-Type)|detail'
echo -e "\n"

echo "=== 7. Field không tồn tại (Mong đợi: 400) ==="
curl -s -w "\nHTTP %{http_code}\n" "$BASE_URL/orders?fields=id,password"
echo

echo "=== 8. Sort field không tồn tại (Mong đợi: 400) ==="
curl -s -w "\nHTTP %{http_code}\n" "$BASE_URL/orders?sort=-price"
