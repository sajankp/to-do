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
    model_config = SettingsConfigDict(env_file=".env")


def get_settings() -> Settings:
    return Settings()
