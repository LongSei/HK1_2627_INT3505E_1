"""Lab 2: 3 helper cho list_books, tách riêng để test đơn lẻ.

- parse_sort:     whitelist sort key, dấu "-" = giảm dần, luôn thêm id làm tie-break
- apply_cursor:   lọc các bản ghi đứng sau cursor theo composite key (sort_value, id)
- build_response: cắt trang, sinh next cursor
"""
import base64
import binascii
import json
from dataclasses import dataclass

from sqlalchemy import tuple_

from models import Book
from routes.common import error

# Whitelist: tên sort client gửi -> cột thật. Không bao giờ đưa chuỗi raw vào order_by()
SORT = {"id": Book.id, "price": Book.price_vnd}


@dataclass
class SortSpec:
    raw: str  # chuỗi client gửi, VD "-price" (lưu vào cursor)
    key: str  # "price"
    column: object  # Book.price_vnd
    desc: bool

    @property
    def order_by(self):
        # Tie-break bằng id, cùng chiều với khoá chính
        if self.desc:
            return [self.column.desc(), Book.id.desc()]
        return [self.column.asc(), Book.id.asc()]

    def value_of(self, book):
        return getattr(book, self.column.key)


def parse_sort(raw):
    """Trả về (SortSpec, None) hoặc (None, response lỗi 400)."""
    if "," in raw:
        return None, error(400, "bad_sort", "Sort nhiều key (VD -price,title) chưa hỗ trợ trong Lab 2", field=["sort"])
    desc = raw.startswith("-")
    key = raw[1:] if desc else raw
    if key not in SORT:
        return None, error(400, "bad_sort", f"sort '{raw}' không hợp lệ. Cho phép: {sorted(SORT)} (thêm '-' để giảm dần)", field=["sort"])
    return SortSpec(raw=raw, key=key, column=SORT[key], desc=desc), None


def _enc(state):
    return base64.urlsafe_b64encode(json.dumps(state).encode()).decode().rstrip("=")


def _dec(token):
    try:
        state = json.loads(base64.urlsafe_b64decode(token + "=" * (-len(token) % 4)))
    except (binascii.Error, ValueError, UnicodeDecodeError):
        return None
    if not isinstance(state, dict) or not {"s", "f", "v", "i"} <= state.keys():
        return None
    if not isinstance(state["v"], int) or not isinstance(state["i"], int):
        return None
    return state


def apply_cursor(q, raw, spec, category):
    """Trả về (query đã lọc, None) hoặc (None, response lỗi 400).

    Cursor bị ràng buộc với sort và filter lúc tạo: đổi sort/filter mà dùng lại cursor cũ -> 400.
    """
    if not raw:
        return q, None
    state = _dec(raw)
    if state is None:
        return None, error(400, "bad_cursor", "cursor không hợp lệ", field=["cursor"])
    if state["s"] != spec.raw:
        return None, error(400, "sort_changed", f"cursor được tạo với sort '{state['s']}', không dùng được với sort '{spec.raw}'", field=["cursor"])
    if state["f"] != category:
        return None, error(400, "filter_changed", "cursor được tạo với filter khác", field=["cursor"])

    # WHERE (price_vnd, id) < (v, i) khi giảm dần; > khi tăng dần
    key = tuple_(spec.column, Book.id)
    last = tuple_(state["v"], state["i"])
    return q.where(key < last if spec.desc else key > last), None


def build_response(rows, limit, spec, category):
    """rows lấy limit + 1 bản ghi: có bản ghi thứ limit + 1 nghĩa là còn trang sau."""
    more = len(rows) > limit
    items = rows[:limit]
    nxt = None
    if items and more:
        last = items[-1]
        nxt = _enc({"s": spec.raw, "f": category, "v": spec.value_of(last), "i": last.id})
    return {"data": [b.to_dict() for b in items], "page": {"next": nxt, "more": more, "limit": limit}}
