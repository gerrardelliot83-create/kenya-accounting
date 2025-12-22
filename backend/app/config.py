"""
Application Configuration Module

Uses pydantic-settings to load configuration from environment variables.
All sensitive configuration should be stored in .env file.
"""

from functools import lru_cache
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Security Notes:
    - Never commit .env file to version control
    - Encryption key must be kept secure and rotated periodically
    - Use different keys for different environments
    """

    # Environment Configuration
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")

    # Application Configuration
    app_name: str = Field(default="Kenya SMB Accounting MVP", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")

    # Server Configuration
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Supabase Configuration
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_anon_key: str = Field(..., alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(..., alias="SUPABASE_SERVICE_ROLE_KEY")

    # Database Configuration
    database_url: str = Field(..., alias="DATABASE_URL")
    database_pool_size: int = Field(default=20, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")

    # JWT Configuration
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS"
    )

    # Encryption Configuration
    encryption_key: str = Field(..., alias="ENCRYPTION_KEY")

    # UploadThing Configuration
    uploadthing_token: str = Field(..., alias="UPLOADTHING_TOKEN")

    # LlamaParse Configuration
    llama_cloud_api_key: str = Field(..., alias="LLAMA_CLOUD_API_KEY")

    # CORS Configuration
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
        ],
        alias="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")

    # Cache Configuration (in-memory, no Redis for MVP)
    cache_default_ttl: int = Field(default=300, alias="CACHE_DEFAULT_TTL")
    cache_max_size: int = Field(default=1000, alias="CACHE_MAX_SIZE")

    # Rate Limiting Configuration
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, alias="RATE_LIMIT_WINDOW")

    # Email Configuration
    smtp_host: str = Field(default="smtp.gmail.com", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(default="noreply@kenyaaccounting.com", alias="SMTP_FROM_EMAIL")
    smtp_from_name: str = Field(default="Kenya SMB Accounting", alias="SMTP_FROM_NAME")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    email_enabled: bool = Field(default=False, alias="EMAIL_ENABLED")

    # Logging Configuration
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v):
        """Validate encryption key meets minimum security requirements."""
        if len(v) < 32:
            raise ValueError(
                "Encryption key must be at least 32 characters for AES-256"
            )
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic migrations."""
        return self.database_url.replace(
            "postgresql+asyncpg://",
            "postgresql://"
        )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are loaded only once.
    This is the recommended way to access settings throughout the application.

    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Create a global settings instance for convenience
settings = get_settings()
