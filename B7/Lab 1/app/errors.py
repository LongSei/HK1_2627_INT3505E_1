from flask import jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException


class Conflict(Exception):
    def __init__(self, message):
        self.message = message


def register_errors(app):
    @app.errorhandler(Conflict)
    def conflict(e):
        return jsonify(error="conflict", detail=e.message), 409

    @app.errorhandler(ValidationError)
    def validation(e):
        return jsonify(error="validation_error", detail=e.messages), 422

    @app.errorhandler(HTTPException)
    def http_error(e):
        return jsonify(error=e.name.lower().replace(" ", "_"), detail=e.description), e.code
