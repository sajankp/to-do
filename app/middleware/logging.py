import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.routers.auth import decode_jwt_token


class StructlogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Clear context from previous requests (critical for contextvars)
        structlog.contextvars.clear_contextvars()

        request_id = str(uuid.uuid4())

        # Bind basic request context
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host,
        )

        # Attempt to extract Session ID (sid) from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_jwt_token(token)
            if payload:
                sid = payload.get("sid")
                if sid:
                    structlog.contextvars.bind_contextvars(sid=sid)

        logger = structlog.get_logger()

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            # If an exception bubbles up, log it before it's handled by other handlers
            structlog.get_logger("middleware").exception("Request failed")
            raise

        process_time = time.perf_counter() - start_time

        # Log completion
        status_code = response.status_code
        logger.info(
            "Request finished",
            status_code=status_code,
            duration=process_time,
        )

        # Add Request ID to response headers for debugging
        response.headers["X-Request-ID"] = request_id

        return response
