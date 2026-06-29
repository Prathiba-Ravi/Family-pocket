import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    """
    Shared config. SECRET_KEY signs nothing security-critical by itself
    (sessions are server-side, looked up by token) but Flask requires one
    for flash messages / CSRF cookie signing helpers.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        # Fail loudly in anything that isn't local dev. A missing secret
        # key silently falling back to a hardcoded default is exactly the
        # kind of mistake this project is meant to teach people to avoid.
        if os.environ.get("FLASK_ENV") == "production":
            raise RuntimeError("SECRET_KEY must be set in production.")
        SECRET_KEY = "dev-only-secret-not-for-production"

    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH", os.path.join(BASE_DIR, "instance", "guardian_ledger.db")
    )
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "instance", "uploads"))
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    SESSION_COOKIE_NAME = "gl_session"
    SESSION_LIFETIME = timedelta(hours=12)
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    CSRF_COOKIE_NAME = "gl_csrf"
    CSRF_HEADER_NAME = "X-CSRF-Token"

    PAIR_CODE_LIFETIME = timedelta(minutes=30)

    # The single switch that flips every deliberately-vulnerable branch in
    # the codebase. Defaults OFF. Each vulnerable branch is commented
    # in-place next to its secure counterpart -- see auth/routes.py,
    # transactions/repositories, and approvals/routes.py.
    VULNERABLE_MODE = os.environ.get("VULNERABLE_MODE", "false").lower() == "true"

    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
