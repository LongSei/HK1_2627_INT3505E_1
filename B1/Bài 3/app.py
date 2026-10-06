# Bài 3: Đọc JSON từ request body, validate, tạo resource trả về 201 Created
from uuid import uuid4

from flask import Flask, jsonify, request

app = Flask(__name__)
app.json.ensure_ascii = False  # trả tiếng Việt có dấu thay vì \uXXXX

STUDENTS = []


@app.route("/students", methods=["POST"])
def create_student():
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    if not name:
        return jsonify({"error": "name là bắt buộc"}), 400

    student = {
        "id": str(uuid4()),
        "name": name,
        "gpa": body.get("gpa", 0.0),
    }
    STUDENTS.append(student)
    # 201 Created + header Location trỏ tới resource mới
    return jsonify(student), 201, {"Location": f"/students/{student['id']}"}


@app.route("/students/<student_id>", methods=["GET"])
def get_student(student_id):
    student = next((s for s in STUDENTS if s["id"] == student_id), None)
    if student is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(student), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)
