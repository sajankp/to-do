from fastapi import Request


def get_mongodb_client(request: Request):
    """FastAPI dependency to inject MongoDB client from app state."""
    return request.app.mongodb_client
