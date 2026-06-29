"""
Transaction business logic. Routes stay thin and only handle HTTP
concerns (parsing the request, calling here, returning the response);
all validation and authorization for transactions lives in this layer,
same as auth_service does for auth.
"""
import os
import secrets

from flask import current_app
from werkzeug.utils import secure_filename

from app.errors import ApiError
from app.repositories import comment_repo, notification_repo, transaction_repo
import re

MAX_MERCHANT_LENGTH = 120
MAX_NOTE_LENGTH = 500
MAX_AMOUNT = 1_000_000
ALLOWED_RECEIPT_TYPES = {"image/jpeg", "image/png", "application/pdf"}
MAX_COMMENT_LENGTH = 500
COUPON_PATTERN = re.compile(r"coupon\s*[:=]\s*([A-Za-z0-9.+%_-]+)", re.IGNORECASE)


def _apply_coupon_stack(amount: float, note: str) -> float:
    """Apply stacked coupon directives embedded in the note.

    Vulnerable mode deliberately treats any `coupon:<value>` token as a
    discount request and ignores the sign when applying it. That means
    `coupon:+10`, `coupon:-10`, and repeated coupons all reduce the
    amount, which makes Burp demos easy: keep adding coupons until the
    total collapses to zero or below.
    """
    adjusted = amount
    for raw_token in COUPON_PATTERN.findall(note or ""):
        token = raw_token.strip().lower()
        if token in {"free", "zer0", "zero"}:
            adjusted = 0.0
            continue

        if token.endswith("%"):
            pct = float(token[:-1].lstrip("+-"))
            adjusted -= adjusted * (pct / 100.0)
            continue

        delta = float(token.lstrip("+-"))
        adjusted -= delta

    return adjusted


def create_transaction(db, child: dict, amount, merchant, note) -> dict:
    """A child files a new spend request. Always created as 'pending',
    always denormalizes parent_id from the child's own row at creation
    time -- no parent_id ever comes from the request body."""
    if child.get("parent_id") is None:
        # Defensive: only reachable if role_required('child') is ever
        # removed from the route, since unpaired accounts can't exist
        # with role='child' in the first place.
        raise ApiError("Only a paired child account can file a transaction.", 400)

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ApiError("Amount must be a number.", 400)

    if current_app.config["VULNERABLE_MODE"]:
        # VULNERABLE: amount bounds aren't enforced at all here. A
        # crafted negative or zero amount is accepted and stored,
        # available for business-logic abuse once it reaches approval
        # (e.g. an "approved" negative amount being summed into a
        # balance elsewhere as if it were a credit).
        pass
    else:
        # SECURE
        if amount <= 0:
            raise ApiError("Amount must be greater than zero.", 400)
        if amount > MAX_AMOUNT:
            raise ApiError("Amount is unreasonably large.", 400)

    merchant = str(merchant).strip()
    if not merchant:
        raise ApiError("Merchant is required.", 400)
    if len(merchant) > MAX_MERCHANT_LENGTH:
        raise ApiError(f"Merchant must be {MAX_MERCHANT_LENGTH} characters or fewer.", 400)

    note = str(note or "").strip()
    if len(note) > MAX_NOTE_LENGTH:
        raise ApiError(f"Note must be {MAX_NOTE_LENGTH} characters or fewer.", 400)

    if current_app.config["VULNERABLE_MODE"]:
        # VULNERABLE: coupon stacking bug. The app re-interprets the
        # note as a discount language and applies every coupon it finds
        # with no cap, no deduping, and no floor at zero. Because the
        # parser also ignores coupon sign, both `+` and `-` tokens act
        # like discounts. This is the exact kind of "one coupon turns
        # into a giant discount" flaw that's easy to demo in Burp.
        amount = _apply_coupon_stack(amount, note)

    # Note/merchant are stored exactly as received -- no HTML stripping,
    # no encoding, no sanitization here. That's intentional: encoding on
    # *output* (the frontend, which React handles by escaping JSX text
    # content by default) is what actually prevents XSS, not mangling
    # data on the way into the database. Keeping storage untouched is
    # also what lets a deliberately vulnerable frontend build later
    # demonstrate stored XSS (e.g. via dangerouslySetInnerHTML) against
    # this exact same backend, with zero backend changes required.
    tx_id = transaction_repo.create(
        db,
        child_id=child["id"],
        parent_id=child["parent_id"],
        amount=amount,
        merchant=merchant,
        note=note,
    )
    notification_repo.create(
        db,
        child["parent_id"],
        "transaction_created",
        f"{child['name']} requested approval for {merchant}.",
    )

    return transaction_repo.serialize(transaction_repo.find_by_id(db, tx_id))


def update_transaction(db, child: dict, tx_id: int, amount, merchant, note) -> dict:
    tx = get_detail(db, child, tx_id)
    if tx["childId"] != child["id"]:
        raise ApiError("You can only edit your own requests.", 403)
    if tx["status"] != "pending":
        raise ApiError("Only pending requests can be edited.", 409)

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ApiError("Amount must be a number.", 400)
    if not current_app.config["VULNERABLE_MODE"]:
        if amount <= 0:
            raise ApiError("Amount must be greater than zero.", 400)
        if amount > MAX_AMOUNT:
            raise ApiError("Amount is unreasonably large.", 400)

    merchant = str(merchant).strip()
    note = str(note or "").strip()
    if not merchant:
        raise ApiError("Merchant is required.", 400)
    if len(merchant) > MAX_MERCHANT_LENGTH:
        raise ApiError(f"Merchant must be {MAX_MERCHANT_LENGTH} characters or fewer.", 400)
    if len(note) > MAX_NOTE_LENGTH:
        raise ApiError(f"Note must be {MAX_NOTE_LENGTH} characters or fewer.", 400)

    if current_app.config["VULNERABLE_MODE"]:
        amount = _apply_coupon_stack(amount, note)

    if not transaction_repo.update_pending(db, tx_id, child["id"], amount, merchant, note):
        raise ApiError("Only pending requests can be edited.", 409)
    notification_repo.create(
        db,
        child["parent_id"],
        "transaction_updated",
        f"{child['name']} updated a pending request for {merchant}.",
    )
    return transaction_repo.serialize(transaction_repo.find_by_id(db, tx_id))


def cancel_transaction(db, child: dict, tx_id: int) -> dict:
    tx = get_detail(db, child, tx_id)
    if tx["childId"] != child["id"]:
        raise ApiError("You can only cancel your own requests.", 403)
    if tx["status"] != "pending":
        raise ApiError("Only pending requests can be canceled.", 409)
    if not transaction_repo.cancel_pending(db, tx_id, child["id"]):
        raise ApiError("Only pending requests can be canceled.", 409)
    notification_repo.create(
        db,
        child["parent_id"],
        "transaction_canceled",
        f"{child['name']} canceled a pending request for {tx['merchant']}.",
    )
    return transaction_repo.serialize(transaction_repo.find_by_id(db, tx_id))


def attach_receipt(db, user: dict, tx_id: int, uploaded_file) -> dict:
    tx = get_detail(db, user, tx_id)
    if tx["childId"] != user["id"]:
        raise ApiError("Only the child who created the request can upload a receipt.", 403)
    if tx["status"] != "pending":
        raise ApiError("Receipts can only be changed while a request is pending.", 409)
    if uploaded_file is None or not uploaded_file.filename:
        raise ApiError("Receipt file is required.", 400)

    content_type = uploaded_file.mimetype or "application/octet-stream"
    if not current_app.config["VULNERABLE_MODE"] and content_type not in ALLOWED_RECEIPT_TYPES:
        raise ApiError("Receipts must be a PDF, PNG, or JPG file.", 400)

    original_name = secure_filename(uploaded_file.filename) or "receipt"
    _, ext = os.path.splitext(original_name)
    stored_name = f"tx-{tx_id}-{secrets.token_urlsafe(12)}{ext.lower()}"
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    uploaded_file.save(os.path.join(upload_dir, stored_name))

    transaction_repo.attach_receipt(db, tx_id, stored_name, original_name, content_type)
    notification_repo.create(
        db,
        tx["parentId"],
        "receipt_uploaded",
        f"{user['name']} uploaded a receipt for {tx['merchant']}.",
    )
    return transaction_repo.serialize(transaction_repo.find_by_id(db, tx_id))


def receipt_path_for(db, user: dict, tx_id: int) -> tuple[str, str, str]:
    tx = get_detail(db, user, tx_id)
    if not tx.get("receiptFilename"):
        raise ApiError("Receipt not found.", 404)
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], tx["receiptFilename"])
    if not os.path.exists(path):
        raise ApiError("Receipt file is missing on disk.", 404)
    return path, tx.get("receiptOriginalName") or "receipt", tx.get("receiptContentType") or "application/octet-stream"


def list_for_user(db, user: dict) -> list[dict]:
    """Parents see every transaction across all their paired children;
    children see only their own."""
    if user["role"] == "parent":
        rows = transaction_repo.find_for_parent(db, user["id"])
    else:
        rows = transaction_repo.find_for_child(db, user["id"])
    return [transaction_repo.serialize(row) for row in rows]


def get_detail(db, user: dict, tx_id: int) -> dict:
    row = transaction_repo.find_by_id(db, tx_id)
    if row is None:
        raise ApiError("Transaction not found.", 404)
    tx = transaction_repo.serialize(row)

    if current_app.config["VULNERABLE_MODE"]:
        # VULNERABLE: classic IDOR. No check that `user` is part of
        # this transaction's family -- any authenticated user can read
        # any other family's transaction details just by incrementing
        # the id in the URL.
        return tx

    # SECURE: only the linked parent or the child who filed it.
    if user["id"] not in (tx["parentId"], tx["childId"]):
        raise ApiError("You don't have access to that transaction.", 403)
    return tx


def add_comment(db, user: dict, tx_id: int, body: str) -> list[dict]:
    tx = get_detail(db, user, tx_id)
    body = str(body or "").strip()
    if not body:
        raise ApiError("Comment cannot be empty.", 400)
    if len(body) > MAX_COMMENT_LENGTH:
        raise ApiError(f"Comment must be {MAX_COMMENT_LENGTH} characters or fewer.", 400)
    comment_repo.create(db, tx_id, user["id"], body)
    recipient_id = tx["parentId"] if user["id"] == tx["childId"] else tx["childId"]
    notification_repo.create(
        db,
        recipient_id,
        "transaction_comment",
        f"{user['name']} commented on {tx['merchant']}.",
    )
    return list_comments(db, user, tx_id)


def list_comments(db, user: dict, tx_id: int) -> list[dict]:
    get_detail(db, user, tx_id)
    rows = comment_repo.find_for_transaction(db, tx_id)
    return [comment_repo.serialize(row) for row in rows]
