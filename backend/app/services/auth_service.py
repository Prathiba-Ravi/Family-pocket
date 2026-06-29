import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash

from app.errors import ApiError
from app.repositories import pair_code_repo, session_repo, user_repo


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    if current_app.config["VULNERABLE_MODE"]:
        # VULNERABLE: fast, unsalted MD5. Crackable offline in seconds
        # with a rainbow table or GPU brute force once the DB leaks.
        return "md5$" + hashlib.md5(password.encode("utf-8")).hexdigest()
    # SECURE: werkzeug's default is salted PBKDF2-SHA256 with a high
    # iteration count — slow on purpose, so brute force doesn't scale.
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith("md5$"):
        return password_hash == "md5$" + hashlib.md5(password.encode("utf-8")).hexdigest()
    return check_password_hash(password_hash, password)


# ---------------------------------------------------------------------------
# Pairing codes
# ---------------------------------------------------------------------------

def generate_pair_code() -> str:
    letters = "ABCDEFGHJKLMNPQRSTUVWXYZ"  # no I/O — avoid confusion w/ 1/0
    digits = "0123456789"
    code = "".join(secrets.choice(letters) for _ in range(3))
    code += "-"
    code += "".join(secrets.choice(digits) for _ in range(3))
    return code


def redeem_pair_code(db, code: str) -> int:
    """Returns parent_id on success, raises ApiError otherwise."""
    entry = pair_code_repo.find_by_code(db, code)
    if entry is None:
        raise ApiError("That pairing code wasn't recognized.", 404)

    if current_app.config["VULNERABLE_MODE"]:
        # VULNERABLE: used/expiry checks skipped entirely — the same
        # code can be redeemed by unlimited children, forever.
        pair_code_repo.mark_used(db, code, used_by=None)
        return entry["parent_id"]

    # SECURE
    if entry["used"]:
        raise ApiError("That pairing code has already been used.", 409)
    expires_at = datetime.fromisoformat(entry["expires_at"])
    if expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise ApiError("That pairing code has expired.", 410)
    return entry["parent_id"]


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def authenticate(db, username: str, password: str):
    """Returns the user Row on success, raises ApiError(401) otherwise."""
    if current_app.config["VULNERABLE_MODE"]:
        # VULNERABLE: classic SQL injection. username/password are
        # spliced directly into the query string. A username of
        # `' OR '1'='1' --` returns the first row in the table and logs
        # the attacker in as whoever that is, no password needed.
        expected_hash = hash_password(password)
        query = (
            f"SELECT * FROM users WHERE username = '{username}' "
            f"AND password_hash = '{expected_hash}'"
        )
        try:
            row = db.execute(query).fetchone()
        except Exception:
            row = None
        # (Vulnerable build also skips proper hash comparison — it's
        # literally comparing the raw password against password_hash,
        # which only "works" because vulnerable registration above can
        # also be made to store things insecurely. Kept deliberately
        # broken to make the bug obvious rather than subtle.)
        if row is None:
            raise ApiError("Username or password doesn't match.", 401)
        return row

    # SECURE: always a parameterized lookup by username only; password
    # is checked separately via constant-time hash comparison so the
    # query itself can never be influenced by user input.
    row = user_repo.find_by_username(db, username)
    if row is None or not verify_password(password, row["password_hash"]):
        raise ApiError("Username or password doesn't match.", 401)
    return row


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

def issue_session(db, user_id: int) -> tuple[str, str]:
    """Creates a session row, returns (raw_session_token, raw_csrf_token)."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = (
        datetime.now(timezone.utc) + current_app.config["SESSION_LIFETIME"]
    ).isoformat()
    session_repo.create(db, user_id, token_hash, expires_at)

    csrf_token = secrets.token_urlsafe(24)
    return raw_token, csrf_token


def revoke_session(db, raw_token: str) -> None:
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    session_repo.delete(db, token_hash)
