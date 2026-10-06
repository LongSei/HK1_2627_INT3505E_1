"""
Error handling thống nhất theo RFC 7807 / RFC 9457 (application/problem+json).
"""
import logging
from uuid import uuid4

from flask import jsonify, request
from werkzeug.exceptions import HTTPException

ERROR_BASE = "https://example.com/problems"
logger = logging.getLogger("api.errors")


class ProblemError(Exception):
    """Exception tiện dụng: raise trong route, handler sẽ đổi thành problem+json."""

    def __init__(self, status, title, detail=None, type_path=None, **extra):
        super().__init__(title)
        self.status = status
        self.title = title
        self.detail = detail
        self.type_path = type_path
        self.extra = extra  # extension members, VD: resource_id


def problem(status, title, detail=None, type_path=None, **extra):
    """Tạo response problem+json với đủ type/title/status/detail/instance."""
    body = {
        "type": f"{ERROR_BASE}/{type_path}" if type_path else "about:blank",
        "title": title,
        "status": status,
        "detail": detail or title,
        "instance": request.path,
    }
    body.update(extra)

    resp = jsonify(body)
    resp.status_code = status
    resp.mimetype = "application/problem+json"
    return resp


def register_error_handlers(app):
    @app.errorhandler(ProblemError)
    def handle_problem_error(err):
        return problem(err.status, err.title, err.detail, err.type_path, **err.extra)

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        # Fallback cho lỗi do Flask/Werkzeug sinh ra: 404 route không tồn tại, 405, 415...
        resp = problem(err.code, err.name, err.description)
        # Giữ các header chuẩn của lỗi gốc, VD: 405 phải có header Allow
        for key, value in err.get_headers():
            if key.lower() != "content-type":
                resp.headers[key] = value
        return resp

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        # Không lộ stack trace cho client: log chi tiết ở server, trả message trung tính + trace_id để tra log
        trace_id = str(uuid4())
        logger.exception("Unhandled error trace_id=%s path=%s", trace_id, request.path)
        return problem(
            500,
            "Internal Server Error",
            "An unexpected error occurred. Please try again later.",
            trace_id=trace_id,
        )
