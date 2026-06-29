import hashlib
from functools import wraps

from flask import current_app, g, request

from app.db import get_db
from app.errors import ApiError
from app.repositories import session_repo, user_repo


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def login_required(view):
    """
    Reads the session cookie, looks up the (non-expired) session, and
    attaches the sanitized user dict to `g.current_user`. Every route
    that isn't login/register should be wrapped in this.
    """

    @wraps(view)
    def wrapped(*args, **kwargs):
        cookie_name = current_app.config["SESSION_COOKIE_NAME"]
        raw_token = request.cookies.get(cookie_name)
        if not raw_token:
            raise ApiError("Not authenticated.", 401)

        db = get_db()
        session_row = session_repo.find_valid(db, _hash_token(raw_token))
        if session_row is None:
            raise ApiError("Session is invalid or has expired.", 401)

        user_row = user_repo.find_by_id(db, session_row["user_id"])
        if user_row is None:
            raise ApiError("Session is invalid or has expired.", 401)

        g.current_user = user_repo.serialize(user_row)
        return view(*args, **kwargs)

    return wrapped


def role_required(role: str):
    """
    Must be stacked UNDER @login_required (closer to the function) so
    g.current_user already exists. This is deliberately the single
    chokepoint for role checks — every Maker-Checker bypass in the
    vulnerable build comes from a route that skips this decorator, not
    from this decorator itself having a bug.
    """

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.current_user.get("role") != role:
                raise ApiError(f"This action requires the '{role}' role.", 403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def csrf_protect(view):
    """
    Double-submit cookie check for state-changing requests. The frontend
    reads the (non-httpOnly) gl_csrf cookie and echoes it back as the
    X-CSRF-Token header; we just confirm they match. Skipped entirely
    when VULNERABLE_MODE is on — see config.VULNERABLE_MODE.
    """

    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_app.config["VULNERABLE_MODE"]:
            # VULNERABLE: no CSRF check at all. Any site can drive a
            # logged-in user's browser into POSTing here via a hidden
            # auto-submitting form, because the session cookie rides
            # along automatically and nothing else is verified.
            return view(*args, **kwargs)

        # SECURE: cookie value must match the custom header value. An
        # attacker's cross-site page can make the browser send the
        # cookie, but it can't read the cookie's value to put in the
        # header (browsers block cross-origin cookie reads).
        cookie_val = request.cookies.get(current_app.config["CSRF_COOKIE_NAME"])
        header_val = request.headers.get(current_app.config["CSRF_HEADER_NAME"])
        if not cookie_val or not header_val or cookie_val != header_val:
            raise ApiError("CSRF token missing or invalid.", 403)
        return view(*args, **kwargs)

    return wrapped
