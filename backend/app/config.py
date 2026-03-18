from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import List
import json

# Always resolve .env from the repo root, regardless of which directory uvicorn is launched from.
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Try to load from .env file if it exists, but don't fail if it's missing
        env_file=".env",
        env_file_encoding="utf-8",
        # Allow system environment variables to override .env settings
        env_nested_delimiter="__",
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    APP_NAME: str = "QIPP Medicines Optimization"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"]

    # ── PostgreSQL ────────────────────────────────────────────────────────────
    DATABASE_URL: str

    # ── MongoDB ───────────────────────────────────────────────────────────────
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "qipp_patients"

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-to-a-secure-random-string-at-least-32-chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Celery ────────────────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── OpenPrescribing ───────────────────────────────────────────────────────
    OPENPRESCRIBING_BASE_URL: str = "https://openprescribing.net/api/1.0"

    # ── Scrapfly ─────────────────────────────────────────────────────────────
    SCRAPFLY_API_KEY: str = ""
    SCRAPFLY_DATA_DIR: str = "./data/scrapfly_cache"

    # ── AI ────────────────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash"

    # ── Email ─────────────────────────────────────────────────────────────────
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "notifications@qipp.health"
    NOTIFICATIONS_EMAIL_ENABLED: bool = False

    # ── Admin seed ────────────────────────────────────────────────────────────
    ADMIN_EMAIL: str = "admin@qipp.nhs.uk"
    ADMIN_PASSWORD: str = "changeme123!"
    ADMIN_LAST_NAME: str = "Admin"

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    # ── South Yorkshire specifics ─────────────────────────────────────────────
    SY_ICB_ODS: str = "QF7"
    SY_SUB_ICB_ODS: str = "02P"
    # Real tenant ID confirmed from Supabase users table (f3eedabc = South Yorkshire ICB)
    SY_TENANT_ID: str = "f3eedabc-dd89-42b2-8800-ea6834ad11e7"


# Instantiate settings. 
# Pydantic will automatically check system environment variables first, 
# then look for a .env file if it exists.
settings = Settings()
