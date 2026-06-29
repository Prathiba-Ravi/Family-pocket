"""
All raw SQL for the approval_logs table. This table is append-only by
convention: there is deliberately no update()/delete() here. Every
approve/deny ATTEMPT gets a row -- successful or blocked -- so the audit
trail shows both what happened and what was tried and stopped.
"""
import sqlite3


def create(
    db: sqlite3.Connection,
    transaction_id: int,
    actor_id: int | None,
    action: str,
    success: bool,
    reason: str | None = None,
    ip_address: str | None = None,
) -> int:
    cur = db.execute(
        "INSERT INTO approval_logs "
        "(transaction_id, actor_id, action, success, reason, ip_address) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (transaction_id, actor_id, action, 1 if success else 0, reason, ip_address),
    )
    db.commit()
    return cur.lastrowid


def find_for_transaction(db: sqlite3.Connection, transaction_id: int) -> list[sqlite3.Row]:
    return db.execute(
        "SELECT * FROM approval_logs WHERE transaction_id = ? "
        "ORDER BY datetime(created_at) ASC, id ASC",
        (transaction_id,),
    ).fetchall()


def serialize(row: sqlite3.Row) -> dict:
    data = dict(row)
    data["transactionId"] = data.pop("transaction_id")
    data["actorId"] = data.pop("actor_id")
    data["success"] = bool(data.pop("success"))
    data["ipAddress"] = data.pop("ip_address")
    data["createdAt"] = data.pop("created_at")
    return data
