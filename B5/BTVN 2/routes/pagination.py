"""BTVN 2: sort nhiều key + phân trang offset / cursor cho GET /books."""
import base64
import json

from sqlalchemy import and_, func, or_, select

from models import Book

# Whitelist sort key -> cột thật
SORT = {"id": Book.id, "price": Book.price_vnd, "title": Book.title, "stock": Book.stock}


def parse_sort(raw):
    """'-price,title' -> [(Book.price_vnd, True), (Book.title, False), (Book.id, True)]. Key sai -> None."""
    keys = []
    for part in raw.split(","):
        desc = part.startswith("-")
        name = part.lstrip("-")
        if name not in SORT:
            return None
        keys.append((SORT[name], desc))
    if all(col is not Book.id for col, _ in keys):
        keys.append((Book.id, keys[0][1]))  # thêm id để thứ tự luôn xác định
    return keys


def order_by(keys):
    return [col.desc() if desc else col.asc() for col, desc in keys]


# ---------------- Offset ---------------- #
def offset_page(session, q, offset, limit):
    total = session.scalar(select(func.count()).select_from(q.order_by(None).subquery()))
    rows = session.scalars(q.offset(offset).limit(limit)).all()
    return {
        "data": [b.to_dict() for b in rows],
        "page": {"strategy": "offset", "offset": offset, "limit": limit, "total": total},
    }


# ---------------- Cursor ---------------- #
def encode_cursor(values):
    return base64.urlsafe_b64encode(json.dumps(values).encode()).decode()


def decode_cursor(cursor):
    try:
        return json.loads(base64.urlsafe_b64decode(cursor))
    except ValueError:
        return None


def after(keys, values):
    """Điều kiện "đứng sau bản ghi cuối trang trước" cho nhiều key, kể cả khi khác chiều:
    (k1 sau v1) OR (k1 = v1 AND k2 sau v2) OR ...
    """
    branches = []
    for i, (col, desc) in enumerate(keys):
        same = [c == v for (c, _), v in zip(keys[:i], values[:i])]
        branches.append(and_(*same, col < values[i] if desc else col > values[i]))
    return or_(*branches)


def cursor_page(session, q, keys, cursor, limit):
    if cursor:
        values = decode_cursor(cursor)
        if not isinstance(values, list) or len(values) != len(keys):
            return None
        q = q.where(after(keys, values))
    rows = session.scalars(q.limit(limit + 1)).all()
    items = rows[:limit]
    next_cursor = None
    if len(rows) > limit:
        last = items[-1]
        next_cursor = encode_cursor([getattr(last, col.key) for col, _ in keys])
    return {
        "data": [b.to_dict() for b in items],
        "page": {"strategy": "cursor", "limit": limit, "next": next_cursor},
    }
