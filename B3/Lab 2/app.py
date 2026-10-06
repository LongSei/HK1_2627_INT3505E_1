"""
Lab 2 - Flask error handler trả về problem+json.
"""
import logging
import os

from flask import Flask, jsonify

from errors import ProblemError, register_error_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = Flask(__name__)
register_error_handlers(app)

USERS = {
    1: {"id": 1, "name": "Alice"},
    2: {"id": 2, "name": "Bob"},
}


@app.get("/users/<int:user_id>")
def get_user(user_id):
    user = USERS.get(user_id)
    if user is None:
        raise ProblemError(
            status=404,
            title="User not found",
            detail=f"User with id {user_id} does not exist.",
            type_path="user-not-found",
            resource_id=user_id,
        )
    return jsonify(user)


@app.get("/boom")
def boom():
    # Route cố tình gây lỗi chưa bắt để kiểm thử handler 500
    return 1 / 0


if __name__ == "__main__":
    # Port 5000 trên macOS hay bị AirPlay chiếm nên mặc định dùng 5001
    app.run(port=int(os.environ.get("PORT", 5001)))
