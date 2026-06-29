from flask import jsonify


class ApiError(Exception):
    """Raise this anywhere in services/routes for a clean JSON error response."""

    def __init__(self, message: str, status_code: int = 400, payload: dict | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}


def register_error_handlers(app) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(err: ApiError):
        body = {"error": err.message, **err.payload}
        return jsonify(body), err.status_code

    @app.errorhandler(404)
    def handle_not_found(_err):
        return jsonify({"error": "Not found."}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(_err):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(Exception)
    def handle_unexpected(err: Exception):
        # Never leak stack traces / internal details to the client.
        app.logger.exception("Unhandled exception")
        return jsonify({"error": "Internal server error."}), 500
