"""
BTVN 1 - Hoàn thiện GET /orders từ Lab 3.

So với Lab 3, bản này thêm:
- Sort nhiều field: sort=status,-total (dấu - = giảm dần)
- Cursor gắn với cả sort lẫn filter: dùng cursor với sort/filter khác -> 400
- Lỗi trả về problem+json thống nhất (errors.py từ Lab 2)
- Header Link rel="next"
"""
import base64
import binascii
import json
import os
import random
from functools import cmp_to_key

from flask import Flask, jsonify, request, url_for

from errors import ProblemError, register_error_handlers

app = Flask(__name__)
register_error_handlers(app)

DEFAULT_LIMIT = 10
MAX_LIMIT = 100
FIELDS = {"id", "customer_id", "status", "product_id", "total"}
STATUSES = ["pending", "paid", "shipped", "cancelled"]
FILTERS = ("status", "customer_id")


def generate_orders(count=50):
    """Dữ liệu mẫu cố định (seed). total là bội số của 5 để có nhiều giá trị trùng nhau."""
    rng = random.Random(42)
    return [
        {
            "id": i,
            "customer_id": rng.randint(101, 110),
            "status": rng.choice(STATUSES),
            "product_id": rng.randint(201, 220),
            "total": float(rng.randint(1, 40) * 5),
        }
        for i in range(1, count + 1)
    ]


ORDERS = generate_orders()


def bad_request(detail):
    return ProblemError(400, "Bad Request", detail, type_path="invalid-query")


# ---------------- Parse query ---------------- #
def parse_limit():
    raw = request.args.get("limit", str(DEFAULT_LIMIT))
    try:
        limit = int(raw)
    except ValueError:
        raise bad_request("limit must be an integer")
    if limit < 1:
        raise bad_request("limit must be >= 1")
    return min(limit, MAX_LIMIT)


def parse_filters():
    filters = {}
    status = request.args.get("status")
    if status:
        if status not in STATUSES:
            raise bad_request(f"status must be one of {STATUSES}")
        filters["status"] = status
    customer_id = request.args.get("customer_id")
    if customer_id:
        try:
            filters["customer_id"] = int(customer_id)
        except ValueError:
            raise bad_request("customer_id must be an integer")
    return filters


def parse_sort():
    """sort=status,-total -> [("status", False), ("total", True)] (True = giảm dần)."""
    sort_param = request.args.get("sort", "id")
    spec = []
    for part in sort_param.split(","):
        part = part.strip()
        desc = part.startswith("-")
        field = part[1:] if desc else part
        if field not in FIELDS:
            raise bad_request(f"Invalid sort field '{field}'. Allowed: {sorted(FIELDS)}")
        if any(f == field for f, _ in spec):
            raise bad_request(f"Duplicate sort field '{field}'")
        spec.append((field, desc))
    # Luôn có id làm khoá phụ cuối cùng để thứ tự là duy nhất (cần cho keyset cursor)
    if not any(f == "id" for f, _ in spec):
        spec.append(("id", False))
    return sort_param, spec


def parse_fields():
    fields = request.args.get("fields")
    if not fields:
        return None
    requested = [f.strip() for f in fields.split(",") if f.strip()]
    unknown = [f for f in requested if f not in FIELDS]
    if unknown:
        raise bad_request(f"Unknown fields {unknown}. Allowed: {sorted(FIELDS)}")
    return requested


# ---------------- Sort + keyset ---------------- #
def sort_values(order, spec):
    return [order[f] for f, _ in spec]


def compare(a, b, spec):
    """So sánh 2 danh sách giá trị sort theo spec. -1: a đứng trước b, 1: a đứng sau b."""
    for x, y, (_, desc) in zip(a, b, spec):
        if x != y:
            before = x < y if not desc else x > y
            return -1 if before else 1
    return 0


# ---------------- Cursor ---------------- #
def encode_cursor(order, sort_param, spec, filters):
    data = {"sort": sort_param, "filters": filters, "values": sort_values(order, spec)}
    # Bỏ padding "=" để cursor đặt thẳng vào URL mà không cần encode
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")


def decode_cursor(cursor, sort_param, spec, filters):
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
    except (binascii.Error, ValueError, UnicodeDecodeError):
        raise bad_request("Invalid cursor")
    if (
        not isinstance(data, dict)
        or not {"sort", "filters", "values"} <= data.keys()
        or not isinstance(data["values"], list)
        or len(data["values"]) != len(spec)
    ):
        raise bad_request("Invalid cursor")
    if data["sort"] != sort_param:
        raise bad_request("Cursor was created with a different sort")
    if data["filters"] != filters:
        raise bad_request("Cursor was created with different filters")
    return data["values"]


@app.get("/orders")
def list_orders():
    limit = parse_limit()
    filters = parse_filters()
    sort_param, spec = parse_sort()
    fields = parse_fields()

    # 1. Filter
    result = [o for o in ORDERS if all(o[k] == v for k, v in filters.items())]

    # 2. Sort
    result.sort(key=cmp_to_key(lambda a, b: compare(sort_values(a, spec), sort_values(b, spec), spec)))

    # 3. Keyset cursor: chỉ giữ các order đứng sau phần tử cuối của trang trước
    cursor = request.args.get("cursor")
    if cursor:
        last = decode_cursor(cursor, sort_param, spec, filters)
        try:
            result = [o for o in result if compare(sort_values(o, spec), last, spec) > 0]
        except TypeError:
            # Giá trị trong cursor sai kiểu (VD chuỗi thay cho số)
            raise bad_request("Invalid cursor")

    page = result[:limit]
    has_next = len(result) > limit
    next_cursor = encode_cursor(page[-1], sort_param, spec, filters) if has_next else None

    # 4. Sparse fieldsets
    data = [{f: o[f] for f in fields} for o in page] if fields else page

    resp = jsonify({
        "data": data,
        "pagination": {"limit": limit, "next_cursor": next_cursor, "has_next": has_next},
    })
    if has_next:
        params = {k: v for k, v in request.args.items() if k != "cursor"}
        next_url = url_for("list_orders", **params, cursor=next_cursor)
        resp.headers["Link"] = f'<{next_url}>; rel="next"'
    return resp


if __name__ == "__main__":
    # Port 5000 trên macOS hay bị AirPlay chiếm nên mặc định dùng 5001
    app.run(port=int(os.environ.get("PORT", 5001)))
