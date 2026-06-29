from flask import Flask, request

from .config import Config
from .db import register_db
from .errors import register_error_handlers
from .utils.logging_config import configure_logging


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    configure_logging(app)
    register_db(app)
    register_error_handlers(app)
    _register_cors(app)
    _register_blueprints(app)

    if app.config["VULNERABLE_MODE"]:
        app.logger.warning(
            "VULNERABLE_MODE is ON. This instance is deliberately insecure "
            "and must never be exposed outside a local demo/teaching environment."
        )

    return app


def _register_cors(app: Flask) -> None:
    """
    Manual CORS handling (no flask-cors dependency). Reflects only the
    configured origin list and, critically, sets
    Access-Control-Allow-Credentials so the session cookie is actually
    sent by the browser on cross-origin requests from the Vite dev server.
    """

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin in app.config["CORS_ORIGINS"]:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = (
                f"Content-Type, {app.config['CSRF_HEADER_NAME']}"
            )
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS"
            )
        return response

    @app.route("/api/<path:_path>", methods=["OPTIONS"])
    def cors_preflight(_path):
        return "", 204


def _register_blueprints(app: Flask) -> None:
    from .auth.routes import auth_bp
    from .pairing.routes import pairing_bp
    from .transactions.routes import transactions_bp
    from .approvals.routes import approvals_bp
    from .users.routes import users_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(pairing_bp, url_prefix="/api/pairing")
    app.register_blueprint(transactions_bp, url_prefix="/api/transactions")
    app.register_blueprint(approvals_bp, url_prefix="/api/transactions")
    app.register_blueprint(users_bp, url_prefix="/api/users")
