from flask import Blueprint, g, request

from app.db import get_db
from app.services import approval_service
from app.utils.decorators import csrf_protect, login_required, role_required
from app.utils.responses import ok

# Registered under url_prefix="/api/transactions" in app/__init__.py, so
# routes here read as /api/transactions/<id>/approve etc. -- matching
# the frontend's api.js decideTransaction() call shape exactly.
approvals_bp = Blueprint("approvals", __name__)


@approvals_bp.post("/<int:tx_id>/approve")
@login_required
@role_required("parent")
@csrf_protect
def approve(tx_id):
    data = request.get_json(silent=True) or {}
    notes = str(data.get("notes", "")).strip() or None

    db = get_db()
    tx = approval_service.decide(db, g.current_user, tx_id, "approve", notes)
    return ok(tx)


@approvals_bp.post("/<int:tx_id>/deny")
@login_required
@role_required("parent")
@csrf_protect
def deny(tx_id):
    data = request.get_json(silent=True) or {}
    notes = str(data.get("notes", "")).strip() or None

    db = get_db()
    tx = approval_service.decide(db, g.current_user, tx_id, "deny", notes)
    return ok(tx)


@approvals_bp.get("/<int:tx_id>/audit-log")
@login_required
def audit_log(tx_id):
    """Immutable approve/deny history for one transaction. Visible to
    the linked parent or the filing child only (enforced in the service
    layer)."""
    db = get_db()
    logs = approval_service.get_audit_log(db, g.current_user, tx_id)
    return ok(logs)
