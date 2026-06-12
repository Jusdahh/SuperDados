import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


@dataclass(frozen=True)
class Settings:
    database_url: str
    hash_salt: str
    app_env: str
    limesurvey_base_url: str
    public_invite_expires_hours: int
    public_cookie_secure: bool


@lru_cache
def get_settings() -> Settings:
    return Settings(
        database_url=normalize_database_url(os.getenv("DATABASE_URL", "sqlite:///./superdados.db")),
        hash_salt=os.getenv("HASH_SALT", "change-me"),
        app_env=os.getenv("APP_ENV", "local"),
        limesurvey_base_url=os.getenv("LIMESURVEY_BASE_URL", "").rstrip("/"),
        public_invite_expires_hours=int(os.getenv("PUBLIC_INVITE_EXPIRES_HOURS", "72")),
        public_cookie_secure=os.getenv("PUBLIC_COOKIE_SECURE", "false").lower() == "true",
    )
