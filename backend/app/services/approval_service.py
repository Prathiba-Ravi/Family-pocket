# """
# Maker-Checker business logic: a parent approves or denies a transaction
# their child filed. Every attempt -- whether it succeeds or gets blocked
# -- is written to approval_logs via approval_log_repo, so the audit trail
# itself demonstrates "the system caught the bypass attempt" rather than
# just describing it.

# Checks performed, in order, for the SECURE path:
#   1. Ownership   -- the acting parent must be the parent linked to this
#                      exact transaction (blocks Parent A deciding on
#                      Parent B's family -- IDOR / cross-tenant access).
#   2. Self-approval guard -- the actor can't be the transaction's own
#                      child_id (defense in depth; role_required('parent')
#                      on the route already rules this out structurally).
#   3. State machine -- only a 'pending' transaction can be decided. Blocks
#                      duplicate approvals, re-deciding an already-decided
#                      transaction, and replays of a stale request.
# """
# from flask import current_app, request

# from app.errors import ApiError
# from app.repositories import approval_log_repo, notification_repo, transaction_repo, user_repo

# VALID_ACTIONS = {"approve": "approved", "deny": "denied"}


# def decide(db, actor: dict, tx_id: int, action: str, notes: str | None = None) -> dict:
#     if action not in VALID_ACTIONS:
#         raise ApiError("Action must be 'approve' or 'deny'.", 400)
#     new_status = VALID_ACTIONS[action]
#     ip_address = request.remote_addr

#     tx_row = transaction_repo.find_by_id(db, tx_id)
#     if tx_row is None:
#         raise ApiError("Transaction not found.", 404)
#     tx = transaction_repo.serialize(tx_row)

#     if current_app.config["VULNERABLE_MODE"]:
#         # VULNERABLE: none of the three checks above run. Any
#         # authenticated parent can decide on any family's transaction
#         # (maker-checker bypass via IDOR), can re-decide an
#         # already-approved/denied transaction any number of times
#         # (duplicate approvals, invalid state transitions, replay), and
#         # the self-approval guard is gone too. Approval still debits the
#         # wallet, but because the balance/limit checks are skipped it can
#         # drive the wallet negative.
#         if action == "approve":
#             child_row = user_repo.find_by_id(db, tx["childId"])
#             if child_row is None:
#                 raise ApiError("Child account not found.", 404)
#             wallet_balance = float(child_row["wallet_balance"] or 0)
#             if wallet_balance < float(tx["amount"]):
#                 approval_log_repo.create(
#                     db,
#                     transaction_id=tx_id,
#                     actor_id=actor["id"],
#                     action=action,
#                     success=False,
#                     reason="blocked: approval would exceed the child's wallet balance",
#                     ip_address=ip_address,
#                 )
#                 raise ApiError("The child's wallet balance is too low for this approval.", 409)

#         transaction_repo.update_status(db, tx_id, new_status, decided_by=actor["id"])
#         if action == "approve":
#             user_repo.adjust_wallet(db, tx["childId"], -float(tx["amount"]))
#             db.commit()
#         approval_log_repo.create(
#             db,
#             transaction_id=tx_id,
#             actor_id=actor["id"],
#             action=action,
#             success=True,
#             reason="VULNERABLE_MODE: ownership/self-approval/state checks skipped.",
#             ip_address=ip_address,
#         )
#         notification_repo.create(
#             db,
#             tx["childId"],
#             f"transaction_{new_status}",
#             f"{actor['name']} {new_status} your request for {tx['merchant']}.",
#         )
#         return transaction_repo.serialize(transaction_repo.find_by_id(db, tx_id))

#     # SECURE -----------------------------------------------------------
#     if tx["parentId"] != actor["id"]:
#         approval_log_repo.create(
#             db,
#             transaction_id=tx_id,
#             actor_id=actor["id"],
#             action=action,
#             success=False,
#             reason="blocked: actor is not the parent linked to this transaction",
#             ip_address=ip_address,
#         )
#         raise ApiError("You can't act on a transaction outside your family.", 403)

#     if tx["childId"] == actor["id"]:
#         approval_log_repo.create(
#             db,
#             transaction_id=tx_id,
#             actor_id=actor["id"],
#             action=action,
#             success=False,
#             reason="blocked: actor matches the transaction's own child_id",
#             ip_address=ip_address,
#         )
#         raise ApiError("You can't approve your own transaction.", 403)

#     if tx["status"] != "pending":
#         approval_log_repo.create(
#             db,
#             transaction_id=tx_id,
#             actor_id=actor["id"],
#             action=action,
#             success=False,
#             reason=f"blocked: status was already '{tx['status']}'",
#             ip_address=ip_address,
#         )
#         raise ApiError(f"This transaction was already {tx['status']}.", 409)

#     child_row = user_repo.find_by_id(db, tx["childId"])
#     if child_row is None:
#         raise ApiError("Child account not found.", 404)

#     if action == "approve":
#         spend_so_far = transaction_repo.approved_spend_for_child(db, tx["childId"])
#         balance_limit = child_row["balance_limit"]
#         wallet_balance = float(child_row["wallet_balance"] or 0)
#         if balance_limit is not None and spend_so_far + float(tx["amount"]) > float(balance_limit):
#             approval_log_repo.create(
#                 db,
#                 transaction_id=tx_id,
#                 actor_id=actor["id"],
#                 action=action,
#                 success=False,
#                 reason="blocked: approval would exceed the child's spending limit",
#                 ip_address=ip_address,
#             )
#             raise ApiError("Approving this would exceed the child's spending limit.", 409)
#         if wallet_balance < float(tx["amount"]):
#             approval_log_repo.create(
#                 db,
#                 transaction_id=tx_id,
#                 actor_id=actor["id"],
#                 action=action,
#                 success=False,
#                 reason="blocked: approval would exceed the child's wallet balance",
#                 ip_address=ip_address,
#             )
#             raise ApiError("The child's wallet balance is too low for this approval.", 409)

#     transaction_repo.update_status(db, tx_id, new_status, decided_by=actor["id"])
#     if action == "approve":
#         user_repo.adjust_wallet(db, tx["childId"], -float(tx["amount"]))
#         db.commit()
#     approval_log_repo.create(
#         db,
#         transaction_id=tx_id,
#         actor_id=actor["id"],
#         action=action,
#         success=True,
#         reason=notes,
#         ip_address=ip_address,
#     )
#     notification_repo.create(
#         db,
#         tx["childId"],
#         f"transaction_{new_status}",
#         f"{actor['name']} {new_status} your request for {tx['merchant']}.",
#     )
#     return transaction_repo.serialize(transaction_repo.find_by_id(db, tx_id))


# def get_audit_log(db, viewer: dict, tx_id: int) -> list[dict]:
#     """Either the linked parent or the filing child can view the
#     immutable decision history for a transaction."""
#     tx_row = transaction_repo.find_by_id(db, tx_id)
#     if tx_row is None:
#         raise ApiError("Transaction not found.", 404)
#     tx = transaction_repo.serialize(tx_row)

#     if viewer["id"] not in (tx["parentId"], tx["childId"]):
#         raise ApiError("You don't have access to this transaction's history.", 403)

#     rows = approval_log_repo.find_for_transaction(db, tx_id)
#     return [approval_log_repo.serialize(row) for row in rows]


"""
Maker-Checker business logic: a parent approves or denies a transaction
their child filed. Every attempt -- whether it succeeds or gets blocked
-- is written to approval_logs via approval_log_repo, so the audit trail
itself demonstrates "the system caught the bypass attempt" rather than
just describing it.

Checks performed, in order, for the SECURE path:
  0. Role        -- the actor must hold the 'parent' role. (Moved here
                     from a route-level @role_required decorator so that
                     VULNERABLE_MODE can demonstrate a child reaching
                     this action directly -- a vertical privilege
                     escalation -- with everything else identical.)
  1. Ownership   -- the acting parent must be the parent linked to this
                     exact transaction (blocks Parent A deciding on
                     Parent B's family -- IDOR / cross-tenant access).
  2. Self-approval guard -- the actor can't be the transaction's own
                     child_id (defense in depth on top of the role
                     check above).
  3. State machine -- only a 'pending' transaction can be decided. Blocks
                     duplicate approvals, re-deciding an already-decided
                     transaction, and replays of a stale request.
"""
from flask import current_app, request

from app.errors import ApiError
from app.repositories import approval_log_repo, notification_repo, transaction_repo, user_repo

VALID_ACTIONS = {"approve": "approved", "deny": "denied"}


def decide(db, actor: dict, tx_id: int, action: str, notes: str | None = None) -> dict:
    if action not in VALID_ACTIONS:
        raise ApiError("Action must be 'approve' or 'deny'.", 400)
    new_status = VALID_ACTIONS[action]
    ip_address = request.remote_addr

    tx_row = transaction_repo.find_by_id(db, tx_id)
    if tx_row is None:
        raise ApiError("Transaction not found.", 404)
    tx = transaction_repo.serialize(tx_row)

    if current_app.config["VULNERABLE_MODE"]:
        # VULNERABLE: role check removed from the route entirely (see
        # approvals/routes.py), and none of the three checks below run
        # either. This means a logged-in CHILD can call this endpoint
        # directly and approve/deny their own (or anyone else's)
        # transaction -- a vertical privilege escalation, since the
        # child is performing an action the UI never gives them a
        # button for and the role system is supposed to forbid
        # entirely. Combined with the missing ownership check, any
        # authenticated user of any role can decide on any family's
        # transaction (maker-checker bypass via IDOR), re-decide an
        # already-approved/denied transaction any number of times
        # (duplicate approvals, invalid state transitions, replay).
        # Approval still debits the wallet, but because the
        # balance/limit checks are skipped it can drive the wallet
        # negative.
        if action == "approve":
            child_row = user_repo.find_by_id(db, tx["childId"])
            if child_row is None:
                raise ApiError("Child account not found.", 404)
            wallet_balance = float(child_row["wallet_balance"] or 0)
            if wallet_balance < float(tx["amount"]):
                approval_log_repo.create(
                    db,
                    transaction_id=tx_id,
                    actor_id=actor["id"],
                    action=action,
                    success=False,
                    reason="blocked: approval would exceed the child's wallet balance",
                    ip_address=ip_address,
                )
                raise ApiError("The child's wallet balance is too low for this approval.", 409)

        transaction_repo.update_status(db, tx_id, new_status, decided_by=actor["id"])
        if action == "approve":
            user_repo.adjust_wallet(db, tx["childId"], -float(tx["amount"]))
            db.commit()
        approval_log_repo.create(
            db,
            transaction_id=tx_id,
            actor_id=actor["id"],
            action=action,
            success=True,
            reason="VULNERABLE_MODE: ownership/self-approval/state checks skipped.",
            ip_address=ip_address,
        )
        notification_repo.create(
            db,
            tx["childId"],
            f"transaction_{new_status}",
            f"{actor['name']} {new_status} your request for {tx['merchant']}.",
        )
        return transaction_repo.serialize(transaction_repo.find_by_id(db, tx_id))

    # SECURE -----------------------------------------------------------
    if actor["role"] != "parent":
        approval_log_repo.create(
            db,
            transaction_id=tx_id,
            actor_id=actor["id"],
            action=action,
            success=False,
            reason="blocked: actor is not a parent",
            ip_address=ip_address,
        )
        raise ApiError("This action requires the 'parent' role.", 403)

    if tx["parentId"] != actor["id"]:
        approval_log_repo.create(
            db,
            transaction_id=tx_id,
            actor_id=actor["id"],
            action=action,
            success=False,
            reason="blocked: actor is not the parent linked to this transaction",
            ip_address=ip_address,
        )
        raise ApiError("You can't act on a transaction outside your family.", 403)

    if tx["childId"] == actor["id"]:
        approval_log_repo.create(
            db,
            transaction_id=tx_id,
            actor_id=actor["id"],
            action=action,
            success=False,
            reason="blocked: actor matches the transaction's own child_id",
            ip_address=ip_address,
        )
        raise ApiError("You can't approve your own transaction.", 403)

    if tx["status"] != "pending":
        approval_log_repo.create(
            db,
            transaction_id=tx_id,
            actor_id=actor["id"],
            action=action,
            success=False,
            reason=f"blocked: status was already '{tx['status']}'",
            ip_address=ip_address,
        )
        raise ApiError(f"This transaction was already {tx['status']}.", 409)

    child_row = user_repo.find_by_id(db, tx["childId"])
    if child_row is None:
        raise ApiError("Child account not found.", 404)

    if action == "approve":
        spend_so_far = transaction_repo.approved_spend_for_child(db, tx["childId"])
        balance_limit = child_row["balance_limit"]
        wallet_balance = float(child_row["wallet_balance"] or 0)
        if balance_limit is not None and spend_so_far + float(tx["amount"]) > float(balance_limit):
            approval_log_repo.create(
                db,
                transaction_id=tx_id,
                actor_id=actor["id"],
                action=action,
                success=False,
                reason="blocked: approval would exceed the child's spending limit",
                ip_address=ip_address,
            )
            raise ApiError("Approving this would exceed the child's spending limit.", 409)
        if wallet_balance < float(tx["amount"]):
            approval_log_repo.create(
                db,
                transaction_id=tx_id,
                actor_id=actor["id"],
                action=action,
                success=False,
                reason="blocked: approval would exceed the child's wallet balance",
                ip_address=ip_address,
            )
            raise ApiError("The child's wallet balance is too low for this approval.", 409)

    transaction_repo.update_status(db, tx_id, new_status, decided_by=actor["id"])
    if action == "approve":
        user_repo.adjust_wallet(db, tx["childId"], -float(tx["amount"]))
        db.commit()
    approval_log_repo.create(
        db,
        transaction_id=tx_id,
        actor_id=actor["id"],
        action=action,
        success=True,
        reason=notes,
        ip_address=ip_address,
    )
    notification_repo.create(
        db,
        tx["childId"],
        f"transaction_{new_status}",
        f"{actor['name']} {new_status} your request for {tx['merchant']}.",
    )
    return transaction_repo.serialize(transaction_repo.find_by_id(db, tx_id))


def get_audit_log(db, viewer: dict, tx_id: int) -> list[dict]:
    """Either the linked parent or the filing child can view the
    immutable decision history for a transaction."""
    tx_row = transaction_repo.find_by_id(db, tx_id)
    if tx_row is None:
        raise ApiError("Transaction not found.", 404)
    tx = transaction_repo.serialize(tx_row)

    if viewer["id"] not in (tx["parentId"], tx["childId"]):
        raise ApiError("You don't have access to this transaction's history.", 403)

    rows = approval_log_repo.find_for_transaction(db, tx_id)
    return [approval_log_repo.serialize(row) for row in rows]