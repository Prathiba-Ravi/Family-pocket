import sqlite3


def create(db: sqlite3.Connection, transaction_id: int, author_id: int, body: str) -> int:
    cur = db.execute(
        "INSERT INTO transaction_comments (transaction_id, author_id, body) VALUES (?, ?, ?)",
        (transaction_id, author_id, body),
    )
    db.commit()
    return cur.lastrowid


def find_for_transaction(db: sqlite3.Connection, transaction_id: int) -> list[sqlite3.Row]:
    return db.execute(
        """
        SELECT c.*, u.name AS author_name, u.role AS author_role
        FROM transaction_comments c
        JOIN users u ON u.id = c.author_id
        WHERE c.transaction_id = ?
        ORDER BY datetime(c.created_at), c.id
        """,
        (transaction_id,),
    ).fetchall()


def serialize(row: sqlite3.Row) -> dict:
    data = dict(row)
    data["transactionId"] = data.pop("transaction_id")
    data["authorId"] = data.pop("author_id")
    data["authorName"] = data.pop("author_name")
    data["authorRole"] = data.pop("author_role")
    data["createdAt"] = data.pop("created_at")
    return data
