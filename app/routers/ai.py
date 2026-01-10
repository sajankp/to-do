"""AI router for Gemini API proxy endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.config import get_settings
from app.models.user import UserInDB
from app.routers.auth import get_current_active_user
from app.utils.rate_limiter import limiter

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


class VoiceRequest(BaseModel):
    """Request model for voice AI endpoint."""

    prompt: str = Field(..., min_length=1, max_length=4096, description="User prompt")
    context: dict | None = Field(None, description="Optional context (e.g., user's todos)")


class VoiceResponse(BaseModel):
    """Response model for voice AI endpoint."""

    response: str = Field(..., description="AI-generated response")
    tokens_used: int = Field(..., description="Tokens used (placeholder for future telemetry)")


def _call_gemini_api(prompt: str, context: dict | None = None) -> tuple[str, int]:
    """Call the Gemini API with the given prompt.

    Args:
        prompt: The user's prompt
        context: Optional context dict (e.g., user's todos)

    Returns:
        Tuple of (response_text, tokens_used)

    Raises:
        HTTPException: If API key not configured or API call fails
    """
    if not settings.gemini_api_key:
        logger.error("GEMINI_API_KEY not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured",
        )

    try:
        # Import here to avoid import errors if google-generativeai not installed
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Build prompt with context if provided
        full_prompt = prompt
        if context:
            context_str = f"Context: {context}\n\n"
            full_prompt = context_str + prompt

        response = model.generate_content(full_prompt)

        # Token counting - placeholder for now, tracked for future telemetry
        # Gemini API doesn't easily expose token counts in basic usage
        tokens_used = 0

        return response.text, tokens_used

    except ImportError:
        logger.error("google-generativeai package not installed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service dependencies not installed",
        ) from None
    except Exception as e:
        logger.exception("Gemini API call failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service error: {str(e)}",
        ) from e


@router.post("/voice", response_model=VoiceResponse)
@limiter.limit(settings.ai_rate_limit)
async def process_voice(
    voice_request: VoiceRequest,
    request: Request,
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
) -> VoiceResponse:
    """Process a voice/text prompt through Gemini AI.

    Requires authentication. Rate limited to 10 requests/minute per user.

    Args:
        voice_request: The voice request containing prompt and optional context
        request: FastAPI request (required for rate limiting)
        current_user: The authenticated user

    Returns:
        VoiceResponse with AI-generated response and token usage
    """
    logger.info(f"AI voice request from user {current_user.username}")

    response_text, tokens_used = _call_gemini_api(voice_request.prompt, voice_request.context)

    return VoiceResponse(response=response_text, tokens_used=tokens_used)
