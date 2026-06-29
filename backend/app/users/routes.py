# from flask import Blueprint, current_app, g, request

# from app.db import get_db
# from app.errors import ApiError
# from app.repositories import notification_repo, user_repo
# from app.utils.decorators import csrf_protect, login_required, role_required
# from app.utils.responses import ok
# from app.utils.validation import validate_name

# users_bp = Blueprint("users", __name__)


# @users_bp.get("/<int:user_id>")
# @login_required
# def get_user(user_id):
#     """
#     Used by the frontend (api.getUserById) wherever a transaction or
#     family list only carries an id and needs the full profile. Access
#     is scoped to "your own family" -- yourself, your linked parent, or
#     (if you're a parent) one of your own children.
#     """
#     db = get_db()
#     current = g.current_user

#     target_row = user_repo.find_by_id(db, user_id)
#     if target_row is None:
#         raise ApiError("User not found.", 404)
#     target = user_repo.serialize(target_row)

#     if current_app.config["VULNERABLE_MODE"]:
#         # VULNERABLE: IDOR. No ownership check at all -- any
#         # authenticated user (parent or child, from any family) can
#         # look up any other user's profile just by incrementing the id
#         # in the URL.
#         return ok(target)

#     # SECURE
#     is_self = target["id"] == current["id"]
#     is_my_linked_parent = current.get("parent_id") == target["id"]
#     is_my_linked_child = target.get("parent_id") == current["id"]
#     if not (is_self or is_my_linked_parent or is_my_linked_child):
#         raise ApiError("You don't have access to that user.", 403)

#     return ok(target)


# @users_bp.put("/me")
# @login_required
# @csrf_protect
# def update_me():
#     data = request.get_json(silent=True) or {}
#     name = validate_name(data.get("name", ""))
#     avatar_url = str(data.get("avatarUrl", "") or "").strip()
#     if len(avatar_url) > 500:
#         raise ApiError("Avatar URL is too long.", 400)

#     db = get_db()
#     user_repo.update_profile(db, g.current_user["id"], name, avatar_url)
#     return ok(user_repo.serialize(user_repo.find_by_id(db, g.current_user["id"])))


# @users_bp.put("/children/<int:child_id>/controls")
# @login_required
# @role_required("parent")
# @csrf_protect
# def update_child_controls(child_id):
#     data = request.get_json(silent=True) or {}
#     try:
#         balance_limit = float(data.get("balanceLimit"))
#         wallet_balance = float(data.get("walletBalance"))
#     except (TypeError, ValueError):
#         raise ApiError("Balance and limit must be numbers.", 400)
#     if balance_limit < 0 or wallet_balance < 0:
#         raise ApiError("Balance and limit cannot be negative.", 400)

#     db = get_db()
#     child = user_repo.find_by_id(db, child_id)
#     if child is None or child["parent_id"] != g.current_user["id"]:
#         raise ApiError("Child account not found.", 404)
#     user_repo.update_child_controls(db, child_id, g.current_user["id"], balance_limit, wallet_balance)
#     notification_repo.create(
#         db,
#         child_id,
#         "wallet_updated",
#         f"{g.current_user['name']} updated your wallet balance or spending limit.",
#     )
#     return ok(user_repo.serialize(user_repo.find_by_id(db, child_id)))


# @users_bp.get("/me/notifications")
# @login_required
# def list_notifications():
#     db = get_db()
#     rows = notification_repo.find_for_user(db, g.current_user["id"])
#     return ok([notification_repo.serialize(row) for row in rows])


# @users_bp.post("/me/notifications/read")
# @login_required
# @csrf_protect
# def read_notifications():
#     db = get_db()
#     notification_repo.mark_all_read(db, g.current_user["id"])
#     return ok({"read": True})



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


@users_bp.delete("/<int:user_id>")
@login_required
def delete_user(user_id):
    """
    Account deletion. Demonstrates broken access control / missing
    ownership check when VULNERABLE_MODE is on.
    """
    db = get_db()
    current = g.current_user

    target_row = user_repo.find_by_id(db, user_id)
    if target_row is None:
        raise ApiError("User not found.", 404)
    target = user_repo.serialize(target_row)

    if current_app.config["VULNERABLE_MODE"]:
        # VULNERABLE: no ownership/role check at all. Any authenticated
        # user -- parent or child, from any family -- can delete any
        # other account just by hitting this endpoint with the right id.
        # No CSRF check either, so this is also reachable via a forged
        # cross-site request if the victim's session cookie is active.
        user_repo.delete(db, user_id)
        db.commit()
        return ok({"deleted": True, "id": user_id})

    # SECURE: you can only delete your own account, and a parent can't
    # be deleted while they still have linked children (would orphan
    # the child's data and break the maker-checker relationship).
    if target["id"] != current["id"]:
        raise ApiError("You can only delete your own account.", 403)

    if current["role"] == "parent":
        children = user_repo.find_children_of(db, current["id"])
        if children:
            raise ApiError(
                "Remove or transfer your linked children before deleting your account.",
                409,
            )

    if user_repo.count_transactions_for(db, current["id"]) > 0:
        raise ApiError(
            "Accounts with transaction history can't be deleted, to preserve the "
            "approval audit trail. This is enforced even though VULNERABLE_MODE "
            "skips it entirely.",
            409,
        )

    user_repo.delete(db, current["id"])
    db.commit()
    response, status = ok({"deleted": True, "id": current["id"]})
    response.delete_cookie(current_app.config["SESSION_COOKIE_NAME"], path="/")
    response.delete_cookie(current_app.config["CSRF_COOKIE_NAME"], path="/")
    return response, status


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