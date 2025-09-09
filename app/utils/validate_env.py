from app.config import settings

def validate_env():
    required_vars = {
        "MONGO_USERNAME": settings.mongo_username,
        "MONGO_PASSWORD": settings.mongo_password,
        "MONGO_HOST": settings.mongo_host,
        "MONGO_DATABASE": settings.mongo_db,
        "MONGO_TODO_COLLECTION": settings.mongo_todo_collection,
        "MONGO_USER_COLLECTION": settings.mongo_user_collection,
    }
    missing = [name for name, value in required_vars.items() if not value]
    if missing:
        raise RuntimeError(f"Missing required MongoDB environment variables: {missing}")
