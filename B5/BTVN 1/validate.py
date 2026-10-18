"""Kiểm tra 3 JSON Schema hợp lệ và validate một ví dụ cho mỗi schema. Chạy: python validate.py"""
import json

from jsonschema import Draft202012Validator

EXAMPLES = {
    "book": {"id": "bk_1", "title": "Lập trình Python", "isbn": "9786043221124", "publishedYear": 2021,
             "authors": [{"id": "au_1", "name": "Nguyễn Văn A"}], "availableCopies": 2},
    "member": {"id": "mem_1", "fullName": "Trần Thị B", "membershipType": "student", "joinedAt": "2026-09-01T02:00:00Z"},
    "loan": {"id": "ln_1", "copyId": "cp_3", "memberId": "mem_1", "borrowedAt": "2026-10-01T08:00:00Z",
             "dueDate": "2026-10-15", "returnedAt": None, "status": "borrowing"},
}

for name, example in EXAMPLES.items():
    schema = json.load(open(f"schemas/{name}.json", encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema).iter_errors(example))
    print(f"{name}.json: schema OK, ví dụ {'hợp lệ' if not errors else errors[0].message}")
