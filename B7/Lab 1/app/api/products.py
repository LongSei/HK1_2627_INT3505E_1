from flask import Blueprint, abort, jsonify, request
from sqlalchemy.exc import IntegrityError

from ..errors import Conflict
from ..extensions import db
from ..models import Product
from ..schemas import ProductIn, ProductOut, ProductPatch, ReserveIn

products_bp = Blueprint("products", __name__, url_prefix="/api/v1/products")


def get_active_or_404(id):
    p = db.session.get(Product, id)
    if p is None or p.archived:
        abort(404, description="product not found")
    return p


@products_bp.get("")
def list_products():
    page = max(1, request.args.get("page", 1, type=int))
    size = min(100, max(1, request.args.get("size", 20, type=int)))
    base = db.select(Product).where(Product.archived.is_(False))
    rows = db.session.execute(base.order_by(Product.id).offset((page - 1) * size).limit(size)).scalars().all()
    total = db.session.scalar(db.select(db.func.count()).select_from(Product).where(Product.archived.is_(False)))
    return jsonify(items=ProductOut(many=True).dump(rows), page=page, size=size, total=total), 200


@products_bp.get("/<int:id>")
def get_product(id):
    return ProductOut().dump(get_active_or_404(id)), 200


@products_bp.post("")
def create_product():
    body = ProductIn().load(request.get_json(silent=True) or {})
    p = Product(**body)
    db.session.add(p)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Conflict("sku already exists")
    return ProductOut().dump(p), 201


@products_bp.post("/<int:id>/reserve")
def reserve_product(id):
    body = ReserveIn().load(request.get_json(silent=True) or {})
    p = get_active_or_404(id)
    if p.qty_in_stock < body["qty"]:
        raise Conflict("not enough stock")
    p.qty_in_stock -= body["qty"]
    db.session.commit()
    return ProductOut().dump(p), 200


@products_bp.patch("/<int:id>")
def patch_product(id):
    body = ProductPatch().load(request.get_json(silent=True) or {}, partial=True)
    p = get_active_or_404(id)
    for k, v in body.items():
        setattr(p, k, v)
    db.session.commit()
    return ProductOut().dump(p), 200


@products_bp.delete("/<int:id>")
def delete_product(id):
    p = get_active_or_404(id)
    p.archived = True
    db.session.commit()
    return "", 204
