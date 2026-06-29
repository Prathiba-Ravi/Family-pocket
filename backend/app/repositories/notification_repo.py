import sqlite3


def create(db: sqlite3.Connection, user_id: int, type_: str, message: str) -> int:
    cur = db.execute(
        "INSERT INTO notifications (user_id, type, message) VALUES (?, ?, ?)",
        (user_id, type_, message),
    )
    db.commit()
    return cur.lastrowid


def find_for_user(db: sqlite3.Connection, user_id: int) -> list[sqlite3.Row]:
    return db.execute(
        """
        SELECT * FROM notifications
        WHERE user_id = ?
        ORDER BY datetime(created_at) DESC, id DESC
        LIMIT 30
        """,
        (user_id,),
    ).fetchall()


def mark_all_read(db: sqlite3.Connection, user_id: int) -> None:
    db.execute("UPDATE notifications SET read = 1 WHERE user_id = ?", (user_id,))
    db.commit()


def serialize(row: sqlite3.Row) -> dict:
    data = dict(row)
    data["userId"] = data.pop("user_id")
    data["createdAt"] = data.pop("created_at")
    data["read"] = bool(data["read"])
    return data
