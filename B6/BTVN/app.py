"""Social Network API - chạy theo openapi.yaml. Chạy: python app.py -> http://127.0.0.1:5001/api/v1"""
import os
import time
from datetime import timedelta

from flask import Flask, jsonify, request
from flask_jwt_extended import (JWTManager, create_access_token, create_refresh_token, decode_token,
                                get_jwt, get_jwt_identity, jwt_required)
from jwt.exceptions import PyJWTError
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config.update(
    JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY", "dev-only-secret-change-me-32-bytes!!"),
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=15),
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=30),
)
app.json.ensure_ascii = False
jwt = JWTManager(app)

# Dữ liệu mẫu. Mật khẩu chỉ lưu dạng hash.
USERS = {
    "an@example.com": {"id": 1, "pwd": generate_password_hash("123456"), "scopes": ["posts:read"]},
    "binh@example.com": {"id": 2, "pwd": generate_password_hash("123456"), "scopes": []},
}
POSTS = {
    1: {"id": 1, "authorId": 1, "content": "Bài công khai của An", "visibility": "public"},
    2: {"id": 2, "authorId": 2, "content": "Bài riêng tư của Bình", "visibility": "private"},
}
REVOKED = set()  # jti của refresh token đã dùng
FAILED = {}  # ip -> danh sách thời điểm đăng nhập sai


def err(status, code, headers=None):
    return jsonify(error=code), status, headers or {}


def issue_tokens(user):
    uid = str(user["id"])
    claims = {"scopes": user["scopes"]}
    return jsonify(
        accessToken=create_access_token(identity=uid, additional_claims=claims),
        refreshToken=create_refresh_token(identity=uid, additional_claims=claims),
        tokenType="Bearer",
        expiresIn=900,
    )


# 401 cho mọi lỗi token, kèm WWW-Authenticate
@jwt.unauthorized_loader
@jwt.invalid_token_loader
def _bad_token(_reason):
    return err(401, "invalid_token", {"WWW-Authenticate": 'Bearer error="invalid_token"'})


@jwt.expired_token_loader
def _expired(_header, _payload):
    return err(401, "token_expired", {"WWW-Authenticate": 'Bearer error="invalid_token"'})


@app.post("/api/v1/auth/login")
def login():
    ip = request.remote_addr
    recent = [t for t in FAILED.get(ip, []) if time.time() - t < 60]
    if len(recent) >= 5:
        return err(429, "too_many_requests", {"Retry-After": "60"})

    body = request.get_json(silent=True) or {}
    if not body.get("email") or not body.get("password"):
        return err(400, "bad_request")

    user = USERS.get(body["email"])
    if not user or not check_password_hash(user["pwd"], body["password"]):
        FAILED[ip] = recent + [time.time()]
        return err(401, "invalid_credentials")  # cùng một lỗi cho sai email hoặc sai mật khẩu
    return issue_tokens(user)


@app.post("/api/v1/auth/refresh")
def refresh():
    token = (request.get_json(silent=True) or {}).get("refreshToken")
    if not token:
        return err(400, "bad_request")
    try:
        claims = decode_token(token)
    except PyJWTError:
        return err(401, "invalid_token")
    if claims.get("type") != "refresh" or claims["jti"] in REVOKED:
        return err(401, "invalid_token")
    REVOKED.add(claims["jti"])  # rotation: refresh token chỉ dùng được 1 lần
    user = next(u for u in USERS.values() if str(u["id"]) == claims["sub"])
    return issue_tokens(user)


@app.get("/api/v1/posts/<int:post_id>")
@jwt_required()
def get_post(post_id):
    if "posts:read" not in get_jwt().get("scopes", []):
        return err(403, "insufficient_scope")
    post = POSTS.get(post_id)
    # Bài private của người khác trả 404 như bài không tồn tại (chống BOLA, không lộ bài có tồn tại)
    if not post or (post["visibility"] == "private" and str(post["authorId"]) != get_jwt_identity()):
        return err(404, "not_found")
    return jsonify(post)


# Docs: Swagger UI đọc openapi.yaml
@app.get("/openapi.yaml")
def spec():
    path = os.path.join(os.path.dirname(__file__), "openapi.yaml")
    return open(path, encoding="utf-8").read(), 200, {"Content-Type": "application/yaml"}


@app.get("/docs")
def docs():
    return """<!doctype html><html><head><meta charset="utf-8"><title>Social Network API</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css"></head><body>
<div id="ui"></div><script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>SwaggerUIBundle({url: "/openapi.yaml", dom_id: "#ui", deepLinking: true});</script></body></html>"""


if __name__ == "__main__":
    app.run(port=5001)
