from pathlib import Path
from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"
    SECRET_KEY: str = "default-insecure-secret-key-change-in-production-min-32-chars"
    ENABLE_DEV_TOKEN_BYPASS: bool = False

    # Network & Hosts
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_URL: Optional[str] = None
    FRONTEND_URL: str = "http://localhost:3000"

    @property
    def api_base_url(self) -> str:
        if self.API_URL:
            return self.API_URL.rstrip("/")
        host = "localhost" if self.API_HOST in ("0.0.0.0", "127.0.0.1") else self.API_HOST
        return f"http://{host}:{self.API_PORT}"

    # Task Queue
    REDIS_URL: str = "redis://redis:6379/0"

    # Supabase Auth & Database
    SUPABASE_URL: str = "https://mock.supabase.co"
    SUPABASE_KEY: str = "mock-key"
    SUPABASE_SERVICE_ROLE_KEY: str = "mock-service-role-key"
    SUPABASE_JWT_SECRET: str = "mock-jwt-secret"
    DATABASE_URL: str = "sqlite:///./test.db"

    # Google Gemini AI
    GEMINI_API_KEY: str = "mock-gemini-key"
    GEMINI_MODEL: str = "gemini-3.8-flash"

    # Payments (Razorpay)
    RAZORPAY_KEY_ID: str = "rzp_test_mock"
    RAZORPAY_KEY_SECRET: str = "mock_secret"
    RAZORPAY_WEBHOOK_SECRET: str = "mock_webhook_secret"

    # Email (Resend)
    EMAIL_PROVIDER: str = "resend"
    RESEND_API_KEY: Optional[str] = None
    EMAIL_FROM: str = "reports@datasecurely.com"

    # Sentry
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    REPORT_STORAGE_PATH: str = "./storage/reports"
    BLOCKED_NETWORKS_FILE: str = "config/blocked-networks.txt"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_dev_token_bypass(self):
        if self.ENABLE_DEV_TOKEN_BYPASS and self.ENVIRONMENT not in ("development", "test"):
            raise ValueError(
                f"FATAL: ENABLE_DEV_TOKEN_BYPASS is set to True, but ENVIRONMENT is '{self.ENVIRONMENT}'. "
                "Dev-token bypass is strictly forbidden in staging or production."
            )
        return self


settings = Settings()
