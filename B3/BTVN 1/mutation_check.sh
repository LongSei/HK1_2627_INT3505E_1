#!/bin/bash
# Gài từng lỗi vào một bản sao của app.py rồi chạy lại test: test tốt phải FAIL với mỗi lỗi.
cd "$(dirname "$0")"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
cp errors.py test_orders.py "$TMP"

check() {
    sed "$2" app.py > "$TMP/app.py"
    echo "$1"
    echo "    -> $(cd "$TMP" && python3 -m pytest -q -p no:cacheprovider 2>&1 | tail -1)"
}

echo "Không gài lỗi"
echo "    -> $(python3 -m pytest -q -p no:cacheprovider 2>&1 | tail -1)"
check "Lỗi 1: keyset dùng >= thay vì > (lặp phần tử)" 's/spec), last, spec) > 0/spec), last, spec) >= 0/'
check "Lỗi 2: bỏ id làm khoá phụ" 's/spec.append(("id", False))/pass/'
check "Lỗi 3: bỏ qua chiều giảm dần" 's/before = x < y if not desc else x > y/before = x < y/'
