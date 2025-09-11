from app.config import Settings, get_settings


def validate_env(settings:Settings | None=None):
    if settings is None:
        settings = get_settings()
    required_vars = {
        "MONGO_USERNAME": settings.mongo_username,
        "MONGO_PASSWORD": settings.mongo_password,
        "MONGO_HOST": settings.mongo_host,
        "MONGO_DATABASE": settings.mongo_db,
        "MONGO_TODO_COLLECTION": settings.mongo_todo_collection,
        "MONGO_USER_COLLECTION": settings.mongo_user_collection,
        "MONGO_TIMEOUT": settings.mongo_timeout,
        "SECRET_KEY": settings.secret_key,
        "PASSWORD_ALGORITHM": settings.password_algorithm,
        "ACCESS_TOKEN_EXPIRE_SECONDS": settings.access_token_expire_seconds,
        "REFRESH_TOKEN_EXPIRE_SECONDS": settings.refresh_token_expire_seconds,
    }
    missing = [name for name, value in required_vars.items() if not value]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {missing}")
    return settings
