import sqlite3


def create(
    db: sqlite3.Connection,
    child_id: int,
    parent_id: int,
    amount: float,
    merchant: str,
    note: str = "",
) -> int:
    cur = db.execute(
        "INSERT INTO transactions (child_id, parent_id, amount, merchant, note) VALUES (?, ?, ?, ?, ?)",
        (child_id, parent_id, amount, merchant, note),
    )
    db.commit()
    return cur.lastrowid


def update_pending(
    db: sqlite3.Connection,
    tx_id: int,
    child_id: int,
    amount: float,
    merchant: str,
    note: str,
) -> bool:
    cur = db.execute(
        """
        UPDATE transactions
        SET amount = ?, merchant = ?, note = ?, updated_at = datetime('now')
        WHERE id = ? AND child_id = ? AND status = 'pending'
        """,
        (amount, merchant, note, tx_id, child_id),
    )
    db.commit()
    return cur.rowcount > 0


def cancel_pending(db: sqlite3.Connection, tx_id: int, child_id: int) -> bool:
    cur = db.execute(
        """
        UPDATE transactions
        SET status = 'canceled', updated_at = datetime('now'), decided_at = datetime('now')
        WHERE id = ? AND child_id = ? AND status = 'pending'
        """,
        (tx_id, child_id),
    )
    db.commit()
    return cur.rowcount > 0


def attach_receipt(
    db: sqlite3.Connection,
    tx_id: int,
    filename: str,
    original_name: str,
    content_type: str,
) -> None:
    db.execute(
        """
        UPDATE transactions
        SET receipt_filename = ?, receipt_original_name = ?, receipt_content_type = ?,
            updated_at = datetime('now')
        WHERE id = ?
        """,
        (filename, original_name, content_type, tx_id),
    )
    db.commit()


def find_for_child(db: sqlite3.Connection, child_id: int) -> list[sqlite3.Row]:
    return db.execute(
        "SELECT * FROM transactions WHERE child_id = ? ORDER BY datetime(created_at) DESC, id DESC",
        (child_id,),
    ).fetchall()


def find_for_parent(db: sqlite3.Connection, parent_id: int) -> list[sqlite3.Row]:
    return db.execute(
        "SELECT * FROM transactions WHERE parent_id = ? ORDER BY datetime(created_at) DESC, id DESC",
        (parent_id,),
    ).fetchall()


def find_by_id(db: sqlite3.Connection, tx_id: int) -> sqlite3.Row | None:
    return db.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,)).fetchone()


def update_status(
    db: sqlite3.Connection, tx_id: int, status: str, decided_by: int
) -> None:
    """
    Moves a transaction out of 'pending'. Always parameterized, always
    stamps decided_at server-side (datetime('now')) rather than trusting
    a client-supplied timestamp.
    """
    db.execute(
        "UPDATE transactions SET status = ?, decided_at = datetime('now'), decided_by = ? "
        "WHERE id = ?",
        (status, decided_by, tx_id),
    )
    db.commit()


def approved_spend_for_child(db: sqlite3.Connection, child_id: int) -> float:
    row = db.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM transactions WHERE child_id = ? AND status = 'approved'",
        (child_id,),
    ).fetchone()
    return float(row["total"] or 0)


def serialize(row: sqlite3.Row) -> dict:
    data = dict(row)
    data["childId"] = data.pop("child_id")
    data["parentId"] = data.pop("parent_id")
    data["createdAt"] = data.pop("created_at")
    data["updatedAt"] = data.pop("updated_at")
    data["decidedAt"] = data.pop("decided_at")
    data["decidedBy"] = data.pop("decided_by")
    data["receiptFilename"] = data.pop("receipt_filename", None)
    data["receiptOriginalName"] = data.pop("receipt_original_name", None)
    data["receiptContentType"] = data.pop("receipt_content_type", None)
    data["hasReceipt"] = bool(data.get("receiptFilename"))
    return data
