"""Application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, HttpUrl, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = Field(..., min_length=32)

    # Database
    database_url: str = Field(..., alias="DATABASE_URL")
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: str = Field(..., alias="REDIS_URL")
    redis_session_ttl: int = 14400  # 4 hours

    # SMS Provider (Bandwidth)
    bandwidth_account_id: str
    bandwidth_username: str
    bandwidth_password: str
    bandwidth_application_id: str
    bandwidth_phone_number: str

    # LLM Providers
    anthropic_api_key: str
    openai_api_key: str
    default_llm_provider: Literal["anthropic", "openai"] = "anthropic"
    default_model: str = "claude-3-5-haiku-20241022"

    # Age Verification (Veriff)
    veriff_api_key: str
    veriff_api_secret: str
    veriff_base_url: HttpUrl = HttpUrl("https://stationapi.veriff.com")

    # Payment (Stripe)
    stripe_secret_key: str
    stripe_publishable_key: str
    stripe_webhook_secret: str
    stripe_price_id_monthly: str
    stripe_price_id_annual: str

    # Monitoring
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: HttpUrl = HttpUrl("https://cloud.langfuse.com")
    sentry_dsn: str | None = None

    # Security
    encryption_key: str = Field(..., min_length=32)
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Compliance
    crisis_hotline_number: str = "988"
    ai_disclosure_interval_hours: int = 3
    allowed_origins: list[str] = ["http://localhost:3000"]

    @validator("allowed_origins", pre=True)
    def parse_allowed_origins(cls, v: str | list[str]) -> list[str]:
        """Parse comma-separated origins."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
