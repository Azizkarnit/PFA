from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List

class Settings(BaseSettings):
    PROJECT_NAME: str = "INS Statistical Survey Collection Platform"
    API_V1_STR: str = "/api/v1"
    # SECURITY: Must be overridden in .env with a strong random value
    SECRET_KEY: str = "super-secret-key-for-jwt-development-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    ALGORITHM: str = "HS256"

    # Database
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

    # URLs — set these in .env for production
    FRONTEND_URL: str = "http://localhost:4200"
    BACKEND_URL: str = "http://localhost:8000"
    EXT_APP_URL: str = "http://localhost:3000"
    EXT_TO_PFA_API_KEY: str = "dev_ext_to_pfa_secret_key"

    # CORS — comma-separated list of allowed origins
    ALLOWED_ORIGINS: str = "http://localhost:4200,http://127.0.0.1:4200"

    # Upload limits (MB)
    MAX_UPLOAD_SIZE_MB: int = 50

    # Rate limiting
    MAX_LOGIN_ATTEMPTS_PER_IP: int = 20
    RATE_LIMIT_WINDOW_MINUTES: int = 15

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

    def get_allowed_origins(self) -> List[str]:
        """Parse comma-separated ALLOWED_ORIGINS into a list."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

settings = Settings()
