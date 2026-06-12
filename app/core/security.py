import hashlib

from app.core.config import get_settings


def hash_value(value: str) -> str:
    normalized = (value or "").strip()
    salt = get_settings().hash_salt
    return hashlib.sha256(f"{salt}:{normalized}".encode("utf-8")).hexdigest()
