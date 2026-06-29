-- Family Pocket schema
-- SQLite. Re-runnable: CREATE TABLE IF NOT EXISTS everywhere.

PRAGMA foreign_keys = ON;

-- One table for both roles. role discriminates 'parent' / 'child'.
-- Children have parent_id set; parents have it NULL.
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    role          TEXT NOT NULL CHECK (role IN ('parent', 'child')),
    name          TEXT NOT NULL,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    parent_id     INTEGER REFERENCES users(id),
    balance_limit REAL,                -- optional per-child spend cap, NULL for parents
    wallet_balance REAL NOT NULL DEFAULT 0,
    avatar_url    TEXT NOT NULL DEFAULT '',
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- A pairing code is minted by a parent and redeemed exactly once by a child.
CREATE TABLE IF NOT EXISTS pair_codes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    code       TEXT NOT NULL UNIQUE,
    parent_id  INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL,
    used       INTEGER NOT NULL DEFAULT 0,   -- 0/1
    used_by    INTEGER REFERENCES users(id)
);

-- The request record. parent_id is denormalized from the child's
-- parent_id at creation time so ownership checks don't need a join.
CREATE TABLE IF NOT EXISTS transactions (
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
);

-- Every approve/deny ATTEMPT, successful or blocked. This is the audit
-- trail that makes the blocked action easy to show in a demo.
CREATE TABLE IF NOT EXISTS approval_logs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER NOT NULL REFERENCES transactions(id),
    actor_id       INTEGER REFERENCES users(id),
    action         TEXT NOT NULL,             -- 'approve' | 'deny'
    success        INTEGER NOT NULL,          -- 0/1
    reason         TEXT,                       -- e.g. 'blocked: not parent of child'
    ip_address     TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS transaction_comments (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER NOT NULL REFERENCES transactions(id),
    author_id      INTEGER NOT NULL REFERENCES users(id),
    body           TEXT NOT NULL,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS notifications (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    type       TEXT NOT NULL,
    message    TEXT NOT NULL,
    read       INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Server-side session tokens. Logout/expiry = delete the row.
CREATE TABLE IF NOT EXISTS sessions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    token_hash TEXT NOT NULL UNIQUE,   -- sha256 of the token; raw token never stored
    user_id    INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_parent_id ON users(parent_id);
CREATE INDEX IF NOT EXISTS idx_transactions_child_id ON transactions(child_id);
CREATE INDEX IF NOT EXISTS idx_transactions_parent_id ON transactions(parent_id);
CREATE INDEX IF NOT EXISTS idx_transaction_comments_tx ON transaction_comments(transaction_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, read);
CREATE INDEX IF NOT EXISTS idx_pair_codes_code ON pair_codes(code);
CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash);
