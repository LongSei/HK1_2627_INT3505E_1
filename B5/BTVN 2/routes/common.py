"""Helper dùng chung cho các route: validate JSON Schema, parse ID có tiền tố, lỗi chuẩn."""
import json
from pathlib import Path

from flask import abort, jsonify, request
from jsonschema import Draft202012Validator

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"
_validators = {}


def get_validator(name):
    if name not in _validators:
        schema = json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))
        _validators[name] = Draft202012Validator(schema)
    return _validators[name]


def validate_body(schema_name):
    """Trả về (payload, None) nếu hợp lệ, hoặc (None, response 400) kèm field + message."""
    payload = request.get_json(silent=True)
    if payload is None:
        return None, error(400, "validation_failed", "Body phải là JSON", field=[])
    errors = sorted(get_validator(schema_name).iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        e = errors[0]
        field = list(e.path)
        if e.validator == "required":
            field.append(e.message.split("'")[1])  # "'title' is a required property"
        return None, error(400, "validation_failed", e.message, field=field)
    return payload, None


def error(status, code, message, **extra):
    return jsonify({"error": code, "message": message, **extra}), status


def parse_id(raw, prefix):
    """'book_42' -> 42. Sai tiền tố hoặc không phải số -> None."""
    if raw is None or not raw.startswith(prefix + "_"):
        return None
    num = raw[len(prefix) + 1:]
    return int(num) if num.isdigit() else None


def get_or_404(model, raw_id, prefix, name):
    from models import db

    pk = parse_id(raw_id, prefix)
    obj = db.session.get(model, pk) if pk is not None else None
    if obj is None:
        resp, status = error(404, "not_found", f"{name} {raw_id} không tồn tại")
        resp.status_code = status
        abort(resp)
    return obj
