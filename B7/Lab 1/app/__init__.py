import os

from flask import Flask

from .errors import register_errors
from .extensions import db


def create_app(config=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///products.db")
    app.config.update(config or {})
    db.init_app(app)
    register_errors(app)

    from .api.products import products_bp
    app.register_blueprint(products_bp)

    with app.app_context():
        db.create_all()
    return app
