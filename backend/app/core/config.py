from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "INS Statistical Survey Collection Platform"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "super-secret-key-for-jwt-development-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    ALGORITHM: str = "HS256"

    # Database
    # Default to local XAMPP MySQL setup (root with no password on localhost:3306)
    # The database name is assumed to be 'pfa_db'
    DATABASE_URL: str = "mysql+pymysql://root@localhost:3306/pfa_db"

    # OTP and Lock configuration
    OTP_EXPIRATION_MINUTES: int = 5
    MAX_LOGIN_ATTEMPTS: int = 3
    ACCOUNT_LOCK_HOURS: int = 24
    PASSWORD_ONLY_DURATION_HOURS: int = 1

    # Email
    EMAIL_PROVIDER: str = "brevo"
    BREVO_API_KEY: Optional[str] = None
    BREVO_SENDER_EMAIL: str = "no-reply@ins.tn"
    BREVO_SENDER_NAME: str = "INS Statistical Portal"
    DEFAULT_LANGUAGE: str = "fr"

    # Redis/Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

settings = Settings()
