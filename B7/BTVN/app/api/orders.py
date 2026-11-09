from flask import Blueprint, abort, request
from sqlalchemy.orm import selectinload

from ..extensions import db
from ..models import Order, OrderItem, Product
from ..schemas import OrderIn, OrderOut

orders_bp = Blueprint("orders", __name__, url_prefix="/api/v1/orders")


def load_order(id):
    order = db.session.scalar(
        db.select(Order).where(Order.id == id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )
    if order is None:
        abort(404, description="order not found")
    return order


@orders_bp.post("")
def create_order():
    body = OrderIn().load(request.get_json(silent=True) or {})
    items = []
    for item in body["items"]:
        product = db.session.get(Product, item["product_id"])
        if product is None or product.archived:
            abort(404, description=f"product {item['product_id']} not found")
        items.append(OrderItem(product=product, qty=item["qty"]))
    order = Order(items=items)
    db.session.add(order)
    db.session.commit()
    return OrderOut().dump(load_order(order.id)), 201


@orders_bp.get("/<int:id>")
def get_order(id):
    return OrderOut().dump(load_order(id)), 200
