# Bài 5: Status codes - DELETE /orders/<id> trả đúng 204 / 404 / 409
from flask import Flask, jsonify

app = Flask(__name__)

# Giả lập DB
ORDERS = {
    "ord_1": {"id": "ord_1", "status": "pending"},
    "ord_2": {"id": "ord_2", "status": "shipped"},
    "ord_3": {"id": "ord_3", "status": "delivered"},
}


@app.route("/orders", methods=["GET"])
def list_orders():
    return jsonify(list(ORDERS.values())), 200


# Tên biến trong URL phải trùng tên tham số của hàm (order_id)
@app.route("/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id):
    order = ORDERS.get(order_id)
    # 404 - không tìm thấy
    if order is None:
        return {"error": "not found"}, 404
    # 409 - business rule: đơn đã giao/đang giao thì không xoá được
    if order["status"] in ("shipped", "delivered"):
        return {"error": "cannot delete"}, 409
    ORDERS.pop(order_id, None)
    # 204 - thành công, không có body
    return "", 204


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)
