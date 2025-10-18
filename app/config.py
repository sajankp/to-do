from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings with environment variable configuration."""
    mongo_username: str = Field(
        ..., env="MONGO_USERNAME", description="MongoDB username"
    )
    mongo_password: str = Field(
        ..., env="MONGO_PASSWORD", description="MongoDB password"
    )
    mongo_host: str = Field(..., env="MONGO_HOST")
    mongo_db: str = Field(..., env="MONGO_DATABASE")
    mongo_todo_collection: str = Field(..., env="MONGO_TODO_COLLECTION")
    mongo_user_collection: str = Field(..., env="MONGO_USER_COLLECTION")
    mongo_timeout: int = Field(..., env="MONGO_TIMEOUT")
    secret_key: str = Field(..., env="SECRET_KEY")
    password_algorithm: str = Field(..., env="PASSWORD_ALGORITHM")
    access_token_expire_seconds: int = Field(..., env="ACCESS_TOKEN_EXPIRE_SECONDS")
    refresh_token_expire_seconds: int = Field(..., env="REFRESH_TOKEN_EXPIRE_SECONDS")

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
