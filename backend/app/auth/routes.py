from flask import Blueprint, current_app, g, request

from app.db import get_db
from app.errors import ApiError
from app.repositories import pair_code_repo, user_repo
from app.services import auth_service
from app.utils.decorators import csrf_protect, login_required
from app.utils.responses import ok
from app.utils.validation import (
    require_fields,
    validate_name,
    validate_pair_code,
    validate_password,
    validate_username,
)

auth_bp = Blueprint("auth", __name__)


def _set_auth_cookies(response, session_token: str, csrf_token: str):
    cfg = current_app.config
    max_age = int(cfg["SESSION_LIFETIME"].total_seconds())

    response.set_cookie(
        cfg["SESSION_COOKIE_NAME"],
        session_token,
        max_age=max_age,
        httponly=True,
        secure=cfg["SESSION_COOKIE_SECURE"],
        samesite=cfg["SESSION_COOKIE_SAMESITE"],
        path="/",
    )
    # NOT httpOnly — the frontend JS must be able to read this one to
    # echo it back as a header (that's the whole double-submit point).
    response.set_cookie(
        cfg["CSRF_COOKIE_NAME"],
        csrf_token,
        max_age=max_age,
        httponly=False,
        secure=cfg["SESSION_COOKIE_SECURE"],
        samesite=cfg["SESSION_COOKIE_SAMESITE"],
        path="/",
    )


def _clear_auth_cookies(response):
    cfg = current_app.config
    response.delete_cookie(cfg["SESSION_COOKIE_NAME"], path="/")
    response.delete_cookie(cfg["CSRF_COOKIE_NAME"], path="/")


@auth_bp.post("/register-parent")
def register_parent():
    data = request.get_json(silent=True) or {}
    require_fields(data, ["name", "username", "password"])

    name = validate_name(data["name"])
    username = validate_username(data["username"])
    password = validate_password(data["password"])

    db = get_db()
    if user_repo.find_by_username(db, username) is not None:
        raise ApiError("That username is already taken.", 409)

    password_hash = auth_service.hash_password(password)
    user_id = user_repo.create_parent(db, name, username, password_hash)

    session_token, csrf_token = auth_service.issue_session(db, user_id)
    response, status = ok(user_repo.serialize(user_repo.find_by_id(db, user_id)), 201)
    _set_auth_cookies(response, session_token, csrf_token)
    return response, status


@auth_bp.post("/register-child")
def register_child():
    data = request.get_json(silent=True) or {}
    require_fields(data, ["name", "username", "password", "pairCode"])

    name = validate_name(data["name"])
    username = validate_username(data["username"])
    password = validate_password(data["password"])
    pair_code = validate_pair_code(data["pairCode"])

    db = get_db()
    if user_repo.find_by_username(db, username) is not None:
        raise ApiError("That username is already taken.", 409)

    parent_id = auth_service.redeem_pair_code(db, pair_code)

    password_hash = auth_service.hash_password(password)
    user_id = user_repo.create_child(db, name, username, password_hash, parent_id)

    if not current_app.config["VULNERABLE_MODE"]:
        pair_code_repo.mark_used(db, pair_code, used_by=user_id)

    session_token, csrf_token = auth_service.issue_session(db, user_id)
    response, status = ok(user_repo.serialize(user_repo.find_by_id(db, user_id)), 201)
    _set_auth_cookies(response, session_token, csrf_token)
    return response, status


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    require_fields(data, ["username", "password"])

    db = get_db()
    user_row = auth_service.authenticate(db, data["username"], data["password"])

    session_token, csrf_token = auth_service.issue_session(db, user_row["id"])
    response, status = ok(user_repo.serialize(user_row))
    _set_auth_cookies(response, session_token, csrf_token)
    return response, status


@auth_bp.post("/logout")
@login_required
@csrf_protect
def logout():
    cfg = current_app.config
    raw_token = request.cookies.get(cfg["SESSION_COOKIE_NAME"])
    db = get_db()
    if raw_token:
        auth_service.revoke_session(db, raw_token)

    response, status = ok({"loggedOut": True})
    _clear_auth_cookies(response)
    return response, status


@auth_bp.get("/me")
@login_required
def me():
    return ok(g.current_user)


@auth_bp.get("/family")
@login_required
def family():
    """
    Parents get the list of their paired children (used by
    ParentDashboard to label transactions and show paired accounts).
    Children get a one-item array with their own linked parent, for
    symmetry, even though the current frontend doesn't call this as a
    child. Always scoped to g.current_user -- there's no id parameter
    to tamper with here, so this endpoint has no IDOR surface by
    construction.
    """
    db = get_db()
    current = g.current_user

    if current["role"] == "parent":
        rows = user_repo.find_children_of(db, current["id"])
        return ok([user_repo.serialize(row) for row in rows])

    parent_row = (
        user_repo.find_by_id(db, current["parent_id"])
        if current.get("parent_id")
        else None
    )
    return ok([user_repo.serialize(parent_row)] if parent_row else [])
