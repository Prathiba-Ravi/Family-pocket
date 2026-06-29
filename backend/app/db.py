import os
import sqlite3

import click
from flask import current_app, g


def get_db() -> sqlite3.Connection:
    """
    Returns a sqlite3 connection scoped to the current request (stored on
    Flask's `g`). Reused across calls within the same request instead of
    opening a new connection per query.
    """
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE_PATH"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exception=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    """Create the schema if it doesn't exist yet. Safe to call repeatedly."""
    db_path = current_app.config["DATABASE_PATH"]
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as f:
        conn.executescript(f.read())
    _migrate_existing_schema(conn)
    conn.commit()
    conn.close()


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _add_column_if_missing(
    conn: sqlite3.Connection, table: str, column: str, definition: str
) -> None:
    if column not in _column_names(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _migrate_transactions_status_check(conn: sqlite3.Connection) -> None:
    create_sql_row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'transactions'"
    ).fetchone()
    if not create_sql_row or "'canceled'" in (create_sql_row[0] or ""):
        return

    conn.commit()
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("ALTER TABLE transactions RENAME TO transactions_old")
    conn.execute(
        """
        CREATE TABLE transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id    INTEGER NOT NULL REFERENCES users(id),
            parent_id   INTEGER NOT NULL REFERENCES users(id),
            amount      REAL NOT NULL,
            merchant    TEXT NOT NULL,
            note        TEXT NOT NULL DEFAULT '',
            receipt_filename TEXT,
            receipt_original_name TEXT,
            receipt_content_type TEXT,
            status      TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'denied', 'canceled')),
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
            decided_at  TEXT,
            decided_by  INTEGER REFERENCES users(id)
        )
        """
    )
    old_cols = _column_names(conn, "transactions_old")
    receipt_cols = (
        "receipt_filename, receipt_original_name, receipt_content_type,"
        if "receipt_filename" in old_cols
        else "NULL, NULL, NULL,"
    )
    updated_expr = "updated_at" if "updated_at" in old_cols else "created_at"
    conn.execute(
        f"""
        INSERT INTO transactions (
            id, child_id, parent_id, amount, merchant, note,
            receipt_filename, receipt_original_name, receipt_content_type,
            status, created_at, updated_at, decided_at, decided_by
        )
        SELECT
            id, child_id, parent_id, amount, merchant, note,
            {receipt_cols}
            status, created_at, {updated_expr}, decided_at, decided_by
        FROM transactions_old
        """
    )
    conn.execute("DROP TABLE transactions_old")
    conn.execute("PRAGMA foreign_keys = ON")


def _migrate_existing_schema(conn: sqlite3.Connection) -> None:
    _add_column_if_missing(conn, "users", "wallet_balance", "REAL NOT NULL DEFAULT 0")
    _add_column_if_missing(conn, "users", "avatar_url", "TEXT NOT NULL DEFAULT ''")

    _add_column_if_missing(conn, "transactions", "receipt_filename", "TEXT")
    _add_column_if_missing(conn, "transactions", "receipt_original_name", "TEXT")
    _add_column_if_missing(conn, "transactions", "receipt_content_type", "TEXT")
    if "updated_at" not in _column_names(conn, "transactions"):
        conn.execute("ALTER TABLE transactions ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''")
        conn.execute(
            "UPDATE transactions SET updated_at = COALESCE(NULLIF(updated_at, ''), created_at, datetime('now'))"
        )
    _migrate_transactions_status_check(conn)
    _repair_transactions_old_references(conn)


def _table_sql(conn: sqlite3.Connection, table: str) -> str:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone()
    return row[0] if row and row[0] else ""


def _repair_transactions_old_references(conn: sqlite3.Connection) -> None:
    """Repair foreign keys left pointing to transactions_old by an early migration.

    SQLite rewrites child-table foreign keys when a referenced table is
    renamed. If a migration then drops the renamed table, inserts into
    those child tables fail with "no such table: main.transactions_old".
    Rebuilding the dependent tables points the FK back at transactions.
    """
    conn.commit()
    conn.execute("PRAGMA foreign_keys = OFF")

    if "transactions_old" in _table_sql(conn, "approval_logs"):
        conn.execute("ALTER TABLE approval_logs RENAME TO approval_logs_old")
        conn.execute(
            """
            CREATE TABLE approval_logs (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER NOT NULL REFERENCES transactions(id),
                actor_id       INTEGER REFERENCES users(id),
                action         TEXT NOT NULL,
                success        INTEGER NOT NULL,
                reason         TEXT,
                ip_address     TEXT,
                created_at     TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            INSERT INTO approval_logs
                (id, transaction_id, actor_id, action, success, reason, ip_address, created_at)
            SELECT id, transaction_id, actor_id, action, success, reason, ip_address, created_at
            FROM approval_logs_old
            """
        )
        conn.execute("DROP TABLE approval_logs_old")

    if "transactions_old" in _table_sql(conn, "transaction_comments"):
        conn.execute("ALTER TABLE transaction_comments RENAME TO transaction_comments_old")
        conn.execute(
            """
            CREATE TABLE transaction_comments (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER NOT NULL REFERENCES transactions(id),
                author_id      INTEGER NOT NULL REFERENCES users(id),
                body           TEXT NOT NULL,
                created_at     TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            INSERT INTO transaction_comments
                (id, transaction_id, author_id, body, created_at)
            SELECT id, transaction_id, author_id, body, created_at
            FROM transaction_comments_old
            """
        )
        conn.execute("DROP TABLE transaction_comments_old")

    conn.execute("PRAGMA foreign_keys = ON")


def register_db(app) -> None:
    app.teardown_appcontext(close_db)

    @app.cli.command("init-db")
    def init_db_command():
        """Flask CLI: `flask init-db` — (re)creates tables, never drops data."""
        init_db()
        click.echo(f"Initialized database at {app.config['DATABASE_PATH']}")

    # Make sure the DB file + tables exist on first run without requiring
    # the developer to remember to run `flask init-db` manually.
    with app.app_context():
        init_db()
