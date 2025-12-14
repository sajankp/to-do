from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable configuration."""

    mongo_username: str = Field(
        ..., validation_alias="MONGO_USERNAME", description="MongoDB username"
    )
    mongo_password: str = Field(
        ..., validation_alias="MONGO_PASSWORD", description="MongoDB password"
    )
    mongo_host: str = Field(..., validation_alias="MONGO_HOST")
    mongo_db: str = Field(..., validation_alias="MONGO_DATABASE")
    mongo_todo_collection: str = Field(..., validation_alias="MONGO_TODO_COLLECTION")
    mongo_user_collection: str = Field(..., validation_alias="MONGO_USER_COLLECTION")
    mongo_timeout: int = Field(..., validation_alias="MONGO_TIMEOUT")
    secret_key: str = Field(..., validation_alias="SECRET_KEY")
    password_algorithm: str = Field(..., validation_alias="PASSWORD_ALGORITHM")
    access_token_expire_seconds: int = Field(..., validation_alias="ACCESS_TOKEN_EXPIRE_SECONDS")
    refresh_token_expire_seconds: int = Field(..., validation_alias="REFRESH_TOKEN_EXPIRE_SECONDS")

    # Rate Limiting
    rate_limit_enabled: bool = Field(True, validation_alias="RATE_LIMIT_ENABLED")
    rate_limit_default: str = Field("100/minute", validation_alias="RATE_LIMIT_DEFAULT")
    rate_limit_auth: str = Field("5/minute", validation_alias="RATE_LIMIT_AUTH")
    redis_url: str | None = Field(None, validation_alias="REDIS_URL")

    # CORS Configuration
    cors_origins: str = Field(
        "*", validation_alias="CORS_ORIGINS", description="Comma-separated list of allowed origins"
    )
    cors_allow_credentials: bool = Field(True, validation_alias="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: str = Field("*", validation_alias="CORS_ALLOW_METHODS")
    cors_allow_headers: str = Field("*", validation_alias="CORS_ALLOW_HEADERS")

    model_config = SettingsConfigDict(env_file=".env")

    def get_cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string to list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def get_cors_methods_list(self) -> list[str]:
        """Parse CORS methods from comma-separated string to list."""
        if self.cors_allow_methods == "*":
            return ["*"]
        return [method.strip() for method in self.cors_allow_methods.split(",") if method.strip()]

    def get_cors_headers_list(self) -> list[str]:
        """Parse CORS headers from comma-separated string to list."""
        if self.cors_allow_headers == "*":
            return ["*"]
        return [header.strip() for header in self.cors_allow_headers.split(",") if header.strip()]


def get_settings() -> Settings:
    return Settings()
