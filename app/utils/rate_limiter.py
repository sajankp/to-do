from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request
from app.config import get_settings

settings = get_settings()

def get_limiter_key(request: Request) -> str:
    """
    Identify the user for rate limiting.
    Uses user_id if authenticated, otherwise falls back to IP address.
    """
    if hasattr(request.state, "user_id") and request.state.user_id:
        return str(request.state.user_id)
    
    # Fallback to IP address
    return get_remote_address(request)

# Initialize Limiter
limiter = Limiter(
    key_func=get_limiter_key,
    default_limits=[settings.rate_limit_default] if settings.rate_limit_enabled else [],
    storage_uri=settings.redis_url if settings.redis_url else "memory://",
    enabled=settings.rate_limit_enabled
)
