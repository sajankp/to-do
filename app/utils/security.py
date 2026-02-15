def is_origin_allowed(origin: str | None, allowed_origins: list[str]) -> bool:
    """Return True when origin is present and trusted by the configured allow-list."""
    if not origin:
        return False
    return "*" in allowed_origins or origin in allowed_origins
