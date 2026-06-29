import re

from app.errors import ApiError

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.]{3,32}$")
PAIR_CODE_RE = re.compile(r"^[A-Z]{3}-\d{3}$")


def require_fields(data: dict, fields: list[str]) -> None:
    if not isinstance(data, dict):
        raise ApiError("Request body must be JSON.", 400)
    missing = [f for f in fields if not str(data.get(f, "")).strip()]
    if missing:
        raise ApiError(f"Missing required field(s): {', '.join(missing)}.", 400)


def validate_username(username: str) -> str:
    username = username.strip()
    if not USERNAME_RE.match(username):
        raise ApiError(
            "Username must be 3-32 characters: letters, numbers, underscore, or period.",
            400,
        )
    return username


def validate_password(password: str) -> str:
    if len(password) < 8:
        raise ApiError("Password must be at least 8 characters.", 400)
    return password


def validate_pair_code(code: str) -> str:
    code = code.strip().upper()
    if not PAIR_CODE_RE.match(code):
        raise ApiError("Pairing code format looks wrong (expected ABC-123).", 400)
    return code


def validate_name(name: str) -> str:
    name = name.strip()
    if not (1 <= len(name) <= 80):
        raise ApiError("Name must be between 1 and 80 characters.", 400)
    return name
