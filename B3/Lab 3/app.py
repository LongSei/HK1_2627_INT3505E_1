"""
Lab 3 - GET /orders với (1) cursor pagination, (2) filter status/customer_id, (3) sort, (4) sparse fieldsets.
"""
import base64
import binascii
import json
import os

from flask import Flask, jsonify, request

app = Flask(__name__)

DEFAULT_LIMIT = 10
MAX_LIMIT = 100
FIELDS = {"id", "customer_id", "status", "product_id", "total"}
STATUSES = {"pending", "paid", "shipped", "cancelled"}

ORDERS = [
    {"id": 1, "customer_id": 101, "status": "paid", "product_id": 201, "total": 150.0},
    {"id": 2, "customer_id": 102, "status": "shipped", "product_id": 202, "total": 45.5},
    {"id": 3, "customer_id": 101, "status": "pending", "product_id": 203, "total": 300.0},
    {"id": 4, "customer_id": 103, "status": "paid", "product_id": 201, "total": 85.0},
    {"id": 5, "customer_id": 104, "status": "cancelled", "product_id": 204, "total": 120.0},
    {"id": 6, "customer_id": 102, "status": "paid", "product_id": 205, "total": 510.0},
    {"id": 7, "customer_id": 105, "status": "shipped", "product_id": 202, "total": 65.0},
    {"id": 8, "customer_id": 101, "status": "paid", "product_id": 206, "total": 210.0},
    {"id": 9, "customer_id": 103, "status": "pending", "product_id": 207, "total": 95.0},
    {"id": 10, "customer_id": 106, "status": "paid", "product_id": 208, "total": 400.0},
    {"id": 11, "customer_id": 102, "status": "paid", "product_id": 201, "total": 150.0},
    {"id": 12, "customer_id": 107, "status": "shipped", "product_id": 209, "total": 85.0},
]


def bad_request(detail):
    resp = jsonify({
        "type": "about:blank",
        "title": "Bad Request",
        "status": 400,
        "detail": detail,
        "instance": request.path,
    })
    resp.status_code = 400
    resp.mimetype = "application/problem+json"
    return resp


# --- Cursor: base64 của {"v": giá trị sort của phần tử cuối, "id": id phần tử cuối, "sort": sort đang dùng} --- #
def encode_cursor(item, sort_param, sort_key):
    data = {"sort": sort_param, "v": item[sort_key], "id": item["id"]}
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()


def decode_cursor(cursor):
    """Trả về dict cursor hoặc None nếu cursor hỏng."""
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
    except (binascii.Error, ValueError, UnicodeDecodeError):
        return None
    if not isinstance(data, dict) or not {"sort", "v", "id"} <= data.keys():
        return None
    return data


@app.get("/orders")
def list_orders():
    # 1. limit: mặc định 10, có giới hạn trên
    try:
        limit = int(request.args.get("limit", DEFAULT_LIMIT))
    except ValueError:
        return bad_request("limit must be an integer")
    if limit < 1:
        return bad_request("limit must be >= 1")
    limit = min(limit, MAX_LIMIT)

    # 2. Filter: status, customer_id
    result = ORDERS
    status = request.args.get("status")
    if status:
        if status not in STATUSES:
            return bad_request(f"status must be one of {sorted(STATUSES)}")
        result = [o for o in result if o["status"] == status]

    customer_id = request.args.get("customer_id")
    if customer_id:
        try:
            cid = int(customer_id)
        except ValueError:
            return bad_request("customer_id must be an integer")
        result = [o for o in result if o["customer_id"] == cid]

    # 3. Sort: sort=total (tăng dần) hoặc sort=-total (giảm dần), mặc định id
    sort_param = request.args.get("sort", "id")
    descending = sort_param.startswith("-")
    sort_key = sort_param.lstrip("-")
    if sort_key not in FIELDS:
        return bad_request(f"Invalid sort field '{sort_key}'. Allowed: {sorted(FIELDS)}")

    # id làm khoá phụ để thứ tự luôn xác định khi giá trị sort trùng nhau
    def key(o):
        return (o[sort_key], o["id"])

    result = sorted(result, key=key, reverse=descending)

    # 4. Cursor: lấy các phần tử nằm sau (v, id) của cursor theo đúng thứ tự sort (keyset)
    cursor = request.args.get("cursor")
    if cursor:
        data = decode_cursor(cursor)
        if data is None:
            return bad_request("Invalid cursor")
        if data["sort"] != sort_param:
            return bad_request("Cursor was created with a different sort")
        last = (data["v"], data["id"])
        result = [o for o in result if (key(o) < last if descending else key(o) > last)]

    page = result[:limit]
    has_next = len(result) > limit
    next_cursor = encode_cursor(page[-1], sort_param, sort_key) if has_next else None

    # 5. Sparse fieldsets: fields=id,total
    fields = request.args.get("fields")
    if fields:
        requested = [f.strip() for f in fields.split(",") if f.strip()]
        unknown = [f for f in requested if f not in FIELDS]
        if unknown:
            return bad_request(f"Unknown fields {unknown}. Allowed: {sorted(FIELDS)}")
        page = [{f: o[f] for f in requested} for o in page]

    return jsonify({
        "data": page,
        "pagination": {"limit": limit, "next_cursor": next_cursor, "has_next": has_next},
    })


if __name__ == "__main__":
    # Port 5000 trên macOS hay bị AirPlay chiếm nên mặc định dùng 5001
    app.run(port=int(os.environ.get("PORT", 5001)))
