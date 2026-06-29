from flask import Blueprint, g, request, send_file

from app.db import get_db
from app.services import transaction_service
from app.utils.decorators import csrf_protect, login_required, role_required
from app.utils.responses import ok
from app.utils.validation import require_fields

transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.get("")
@login_required
def list_transactions():
    """Parents get every transaction across all their paired children;
    children get only their own. (See transaction_service.list_for_user
    for the role split.)"""
    db = get_db()
    return ok(transaction_service.list_for_user(db, g.current_user))


@transactions_bp.post("")
@login_required
@role_required("child")
@csrf_protect
def create_transaction():
    data = request.get_json(silent=True) or {}
    require_fields(data, ["amount", "merchant"])

    db = get_db()
    tx = transaction_service.create_transaction(
        db,
        child=g.current_user,
        amount=data["amount"],
        merchant=data["merchant"],
        note=data.get("note", ""),
    )
    return ok(tx, 201)


@transactions_bp.put("/<int:tx_id>")
@login_required
@role_required("child")
@csrf_protect
def update_transaction(tx_id):
    data = request.get_json(silent=True) or {}
    require_fields(data, ["amount", "merchant"])

    db = get_db()
    tx = transaction_service.update_transaction(
        db,
        child=g.current_user,
        tx_id=tx_id,
        amount=data["amount"],
        merchant=data["merchant"],
        note=data.get("note", ""),
    )
    return ok(tx)


@transactions_bp.post("/<int:tx_id>/cancel")
@login_required
@role_required("child")
@csrf_protect
def cancel_transaction(tx_id):
    db = get_db()
    tx = transaction_service.cancel_transaction(db, g.current_user, tx_id)
    return ok(tx)


@transactions_bp.post("/<int:tx_id>/receipt")
@login_required
@role_required("child")
@csrf_protect
def upload_receipt(tx_id):
    db = get_db()
    tx = transaction_service.attach_receipt(db, g.current_user, tx_id, request.files.get("receipt"))
    return ok(tx)


@transactions_bp.get("/<int:tx_id>/receipt")
@login_required
def download_receipt(tx_id):
    db = get_db()
    path, original_name, content_type = transaction_service.receipt_path_for(db, g.current_user, tx_id)
    return send_file(path, mimetype=content_type, as_attachment=False, download_name=original_name)


@transactions_bp.get("/<int:tx_id>/comments")
@login_required
def list_comments(tx_id):
    db = get_db()
    return ok(transaction_service.list_comments(db, g.current_user, tx_id))


@transactions_bp.post("/<int:tx_id>/comments")
@login_required
@csrf_protect
def add_comment(tx_id):
    data = request.get_json(silent=True) or {}
    require_fields(data, ["body"])

    db = get_db()
    return ok(transaction_service.add_comment(db, g.current_user, tx_id, data["body"]), 201)


@transactions_bp.get("/<int:tx_id>")
@login_required
def get_transaction(tx_id):
    """Single-transaction detail view. Authorization (only the linked
    parent or the filing child) is enforced in the service layer so the
    same chokepoint covers both this route and any future one that
    needs a single transaction."""
    db = get_db()
    tx = transaction_service.get_detail(db, g.current_user, tx_id)
    return ok(tx)
