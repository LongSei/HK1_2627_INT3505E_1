# Bài 1: Hello API - endpoint đầu tiên trả JSON
from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    # Flask 3.x tự chuyển dict -> JSON và đặt Content-Type: application/json
    return {"message": "Hello, API!"}


if __name__ == "__main__":
    # Port 5000 trên macOS bị AirPlay chiếm nên dùng 5001
    app.run(host="127.0.0.1", port=5001)
