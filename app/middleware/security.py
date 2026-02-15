from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # OWASP Secure Headers
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS (Strict-Transport-Security) - Only over HTTPS
        if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # CSP: Default to self, allow WebSocket to self (needed for Gemini voice stream)
        # connects to ws:// or wss:// on same origin
        settings = get_settings()
        csp = (
            "default-src 'self'; "
            "connect-src 'self' ws: wss:; "
            f"img-src 'self' data: {settings.csp_img_src}; "
            f"style-src 'self' 'unsafe-inline' {settings.csp_style_src}; "
            f"script-src 'self' 'unsafe-inline' {settings.csp_script_src}; "
            f"font-src 'self' {settings.csp_font_src}; "
        )
        response.headers["Content-Security-Policy"] = csp.strip()

        return response
