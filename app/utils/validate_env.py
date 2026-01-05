from app.config import Settings, get_settings


def validate_env(settings: Settings | None = None):
    if settings is None:
        settings = get_settings()

    # Check MongoDB configuration: either MONGO_URI or individual fields
    has_mongo_uri = bool(settings.mongo_uri)
    has_mongo_individual = all(
        [
            settings.mongo_username,
            settings.mongo_password,
            settings.mongo_host,
        ]
    )

    if not has_mongo_uri and not has_mongo_individual:
        raise RuntimeError(
            "Missing MongoDB configuration: provide either MONGO_URI or "
            "all of MONGO_USERNAME, MONGO_PASSWORD, and MONGO_HOST"
        )

    # Check other required variables
    required_vars = {
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
