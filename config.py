from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    secret_key: str = Field(..., min_length=32,
                            description="Secret key for JWT encoding")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration in minutes")
    refresh_token_expire_days: int = Field(
        default=7, description="Refresh token expiration in days")

    database_url: str = Field(...,
                              description="PostgreSQL database connection URL")

    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    project_name: str = Field(
        default="Auth Microservice", description="Project name")

    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )

    rate_limit_per_minute: int = Field(
        default=10, description="Rate limit per minute for login endpoint")

    environment: str = Field(
        default="development", description="Environment (development, production, testing)")
    debug: bool = Field(default=True, description="Debug mode")

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
