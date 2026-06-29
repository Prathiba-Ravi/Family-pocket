from datetime import datetime, timezone

from flask import Blueprint, current_app, g

from app.db import get_db
from app.repositories import pair_code_repo
from app.services.auth_service import generate_pair_code
from app.utils.decorators import csrf_protect, login_required, role_required
from app.utils.responses import ok

pairing_bp = Blueprint("pairing", __name__)


@pairing_bp.post("/generate")
@login_required
@role_required("parent")
@csrf_protect
def generate():
    db = get_db()
    code = generate_pair_code()
    expires_at = datetime.now(timezone.utc) + current_app.config["PAIR_CODE_LIFETIME"]

    pair_code_repo.create(db, g.current_user["id"], code, expires_at.isoformat())

    return ok({"code": code, "expiresAt": expires_at.isoformat()}, 201)
