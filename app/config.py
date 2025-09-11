from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    mongo_username: str = Field(..., env="MONGO_USERNAME")
    mongo_password: str = Field(..., env="MONGO_PASSWORD")
    mongo_host: str = Field(..., env="MONGO_HOST")
    mongo_db: str = Field(..., env="MONGO_DATABASE")
    mongo_todo_collection: str = Field(..., env="MONGO_TODO_COLLECTION")
    mongo_user_collection: str = Field(..., env="MONGO_USER_COLLECTION")
    mongo_timeout: int = Field(..., env="MONGO_TIMEOUT")

    class Config:
        env_file = ".env"

settings = Settings()
