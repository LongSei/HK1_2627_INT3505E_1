from marshmallow import Schema, fields, validate


class ProductOut(Schema):
    id = fields.Int()
    sku = fields.Str()
    name = fields.Str()
    description = fields.Str(allow_none=True)
    price_cents = fields.Int()
    qty_in_stock = fields.Int()
    archived = fields.Bool()


class ProductIn(Schema):
    sku = fields.Str(required=True, validate=validate.Length(min=3, max=32))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    price_cents = fields.Int(required=True, validate=validate.Range(min=0))
    qty_in_stock = fields.Int(load_default=0, validate=validate.Range(min=0))


class ProductPatch(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=255))
    price_cents = fields.Int(validate=validate.Range(min=0))


class ReserveIn(Schema):
    qty = fields.Int(required=True, validate=validate.Range(min=1))


class OrderItemIn(Schema):
    product_id = fields.Int(required=True)
    qty = fields.Int(required=True, validate=validate.Range(min=1))


class OrderIn(Schema):
    items = fields.List(fields.Nested(OrderItemIn), required=True, validate=validate.Length(min=1))


class OrderItemOut(Schema):
    id = fields.Int()
    qty = fields.Int()
    product = fields.Nested(ProductOut(only=("id", "sku", "name")))


class OrderOut(Schema):
    id = fields.Int()
    items = fields.List(fields.Nested(OrderItemOut))
