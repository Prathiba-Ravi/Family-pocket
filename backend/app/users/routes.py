from flask import Blueprint, current_app, g, request

from app.db import get_db
from app.errors import ApiError
from app.repositories import notification_repo, user_repo
from app.utils.decorators import csrf_protect, login_required, role_required
from app.utils.responses import ok
from app.utils.validation import validate_name

users_bp = Blueprint("users", __name__)


@users_bp.get("/<int:user_id>")
@login_required
def get_user(user_id):
    """
    Used by the frontend (api.getUserById) wherever a transaction or
    family list only carries an id and needs the full profile. Access
    is scoped to "your own family" -- yourself, your linked parent, or
    (if you're a parent) one of your own children.
    """
    db = get_db()
    current = g.current_user

    target_row = user_repo.find_by_id(db, user_id)
    if target_row is None:
        raise ApiError("User not found.", 404)
    target = user_repo.serialize(target_row)

    if current_app.config["VULNERABLE_MODE"]:
        # VULNERABLE: IDOR. No ownership check at all -- any
        # authenticated user (parent or child, from any family) can
        # look up any other user's profile just by incrementing the id
        # in the URL.
        return ok(target)

    # SECURE
    is_self = target["id"] == current["id"]
    is_my_linked_parent = current.get("parent_id") == target["id"]
    is_my_linked_child = target.get("parent_id") == current["id"]
    if not (is_self or is_my_linked_parent or is_my_linked_child):
        raise ApiError("You don't have access to that user.", 403)

    return ok(target)


@users_bp.put("/me")
@login_required
@csrf_protect
def update_me():
    data = request.get_json(silent=True) or {}
    name = validate_name(data.get("name", ""))
    avatar_url = str(data.get("avatarUrl", "") or "").strip()
    if len(avatar_url) > 500:
        raise ApiError("Avatar URL is too long.", 400)

    db = get_db()
    user_repo.update_profile(db, g.current_user["id"], name, avatar_url)
    return ok(user_repo.serialize(user_repo.find_by_id(db, g.current_user["id"])))


@users_bp.put("/children/<int:child_id>/controls")
@login_required
@role_required("parent")
@csrf_protect
def update_child_controls(child_id):
    data = request.get_json(silent=True) or {}
    try:
        balance_limit = float(data.get("balanceLimit"))
        wallet_balance = float(data.get("walletBalance"))
    except (TypeError, ValueError):
        raise ApiError("Balance and limit must be numbers.", 400)
    if balance_limit < 0 or wallet_balance < 0:
        raise ApiError("Balance and limit cannot be negative.", 400)

    db = get_db()
    child = user_repo.find_by_id(db, child_id)
    if child is None or child["parent_id"] != g.current_user["id"]:
        raise ApiError("Child account not found.", 404)
    user_repo.update_child_controls(db, child_id, g.current_user["id"], balance_limit, wallet_balance)
    notification_repo.create(
        db,
        child_id,
        "wallet_updated",
        f"{g.current_user['name']} updated your wallet balance or spending limit.",
    )
    return ok(user_repo.serialize(user_repo.find_by_id(db, child_id)))


@users_bp.get("/me/notifications")
@login_required
def list_notifications():
    db = get_db()
    rows = notification_repo.find_for_user(db, g.current_user["id"])
    return ok([notification_repo.serialize(row) for row in rows])


@users_bp.post("/me/notifications/read")
@login_required
@csrf_protect
def read_notifications():
    db = get_db()
    notification_repo.mark_all_read(db, g.current_user["id"])
    return ok({"read": True})
