"""
All raw SQL for the users table lives here, and only here. Routes/services
never write SQL directly — that one rule is what makes the SQLi contrast
in vulnerable mode easy to point at later: the vulnerable branch is the
only place that deviates from "always go through this repository with a
parameter tuple."
"""
import sqlite3


def find_by_username(db: sqlite3.Connection, username: str) -> sqlite3.Row | None:
    return db.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()


def find_by_id(db: sqlite3.Connection, user_id: int) -> sqlite3.Row | None:
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def create_parent(db: sqlite3.Connection, name: str, username: str, password_hash: str) -> int:
    cur = db.execute(
        "INSERT INTO users (role, name, username, password_hash) "
        "VALUES ('parent', ?, ?, ?)",
        (name, username, password_hash),
    )
    db.commit()
    return cur.lastrowid


def create_child(
    db: sqlite3.Connection,
    name: str,
    username: str,
    password_hash: str,
    parent_id: int,
    balance_limit: float = 200.0,
) -> int:
    cur = db.execute(
        "INSERT INTO users (role, name, username, password_hash, parent_id, balance_limit) "
        "VALUES ('child', ?, ?, ?, ?, ?)",
        (name, username, password_hash, parent_id, balance_limit),
    )
    db.commit()
    return cur.lastrowid


def find_children_of(db: sqlite3.Connection, parent_id: int) -> list[sqlite3.Row]:
    return db.execute(
        "SELECT * FROM users WHERE parent_id = ? ORDER BY created_at", (parent_id,)
    ).fetchall()


def update_profile(db: sqlite3.Connection, user_id: int, name: str, avatar_url: str) -> None:
    db.execute(
        "UPDATE users SET name = ?, avatar_url = ? WHERE id = ?",
        (name, avatar_url, user_id),
    )
    db.commit()


def update_child_controls(
    db: sqlite3.Connection, child_id: int, parent_id: int, balance_limit: float, wallet_balance: float
) -> None:
    db.execute(
        "UPDATE users SET balance_limit = ?, wallet_balance = ? WHERE id = ? AND parent_id = ?",
        (balance_limit, wallet_balance, child_id, parent_id),
    )
    db.commit()


def adjust_wallet(db: sqlite3.Connection, user_id: int, delta: float) -> None:
    db.execute(
        "UPDATE users SET wallet_balance = wallet_balance + ? WHERE id = ?",
        (delta, user_id),
    )


def serialize(user_row: sqlite3.Row | None) -> dict | None:
    """Never return password_hash to a client. This is the single chokepoint
    every route should pass user rows through before jsonify-ing them."""
    if user_row is None:
        return None
    d = dict(user_row)
    d.pop("password_hash", None)
    return d
