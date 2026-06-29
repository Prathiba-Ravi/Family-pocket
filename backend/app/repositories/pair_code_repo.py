import sqlite3


def create(db: sqlite3.Connection, parent_id: int, code: str, expires_at: str) -> None:
    db.execute(
        "INSERT INTO pair_codes (code, parent_id, expires_at) VALUES (?, ?, ?)",
        (code, parent_id, expires_at),
    )
    db.commit()


def find_by_code(db: sqlite3.Connection, code: str) -> sqlite3.Row | None:
    return db.execute(
        "SELECT * FROM pair_codes WHERE code = ?", (code,)
    ).fetchone()


def mark_used(db: sqlite3.Connection, code: str, used_by: int) -> None:
    db.execute(
        "UPDATE pair_codes SET used = 1, used_by = ? WHERE code = ?",
        (used_by, code),
    )
    db.commit()
