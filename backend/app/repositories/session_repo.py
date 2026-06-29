import sqlite3


def create(db: sqlite3.Connection, user_id: int, token_hash: str, expires_at: str) -> None:
    db.execute(
        "INSERT INTO sessions (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
        (user_id, token_hash, expires_at),
    )
    db.commit()


def find_valid(db: sqlite3.Connection, token_hash: str) -> sqlite3.Row | None:
    """Returns the session row only if it exists AND hasn't expired."""
    return db.execute(
        "SELECT * FROM sessions WHERE token_hash = ? AND expires_at > datetime('now')",
        (token_hash,),
    ).fetchone()


def delete(db: sqlite3.Connection, token_hash: str) -> None:
    db.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
    db.commit()
