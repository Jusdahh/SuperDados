from datetime import datetime, timezone
import re
import secrets
import string

from sqlalchemy.orm import Session

from app.core.security import hash_value
from app.models import InviteStatus, SurveyInvite, utc_now


def generate_invite_token() -> str:
    alphabet = string.ascii_letters + string.digits + "_"
    return "".join(secrets.choice(alphabet) for _ in range(32))


def is_limesurvey_token_compatible(token: str | None) -> bool:
    if not token:
        return False
    return bool(re.fullmatch(r"[0-9A-Za-z_]{1,36}", token))


def normalize_dt(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def find_invite_by_token(db: Session, token: str) -> SurveyInvite | None:
    return db.query(SurveyInvite).filter(SurveyInvite.token_hash == hash_value(token)).first()


def is_expired(invite: SurveyInvite) -> bool:
    expires_at = normalize_dt(invite.expires_at)
    return bool(expires_at and expires_at <= utc_now())


def validate_open(
    db: Session,
    *,
    token: str,
    ip: str,
    user_agent: str,
    device_fingerprint: str,
) -> tuple[bool, str | None, SurveyInvite | None]:
    invite = find_invite_by_token(db, token)
    if invite is None:
        return False, "token_not_found", None

    if is_expired(invite):
        invite.status = InviteStatus.expired.value
        db.flush()
        return False, "token_expired", invite

    if invite.status == InviteStatus.completed.value:
        return False, "token_completed", invite
    if invite.status == InviteStatus.blocked.value:
        return False, "token_blocked", invite
    if invite.status == InviteStatus.expired.value:
        return False, "token_expired", invite

    ip_hash = hash_value(ip)
    user_agent_hash = hash_value(user_agent)
    device_hash = hash_value(device_fingerprint)

    if invite.first_device_hash and invite.first_device_hash != device_hash:
        invite.status = InviteStatus.blocked.value
        db.flush()
        return False, "device_mismatch", invite

    if invite.first_opened_at is None:
        invite.first_opened_at = utc_now()
        invite.first_ip_hash = ip_hash
        invite.first_user_agent_hash = user_agent_hash
        invite.first_device_hash = device_hash
        invite.status = InviteStatus.opened.value
        db.flush()

    return True, None, invite
