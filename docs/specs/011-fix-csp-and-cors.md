# Spec-011: Fix CSP and CORS for Docs and Frontend

## Problem Statement
1.  **CSP Blocking Docs**: The current Content Security Policy (CSP) is too strict, blocking resources required by Swagger UI and ReDoc (Google Fonts, jsdelivr, FastAPI favicon). This makes the API documentation unusable.
2.  **CORS Error**: The deployed frontend at `https://sajankp.github.io` is receiving CORS errors when communicating with the backend at `https://to-do-4w0k.onrender.com`.

## Proposed Solution

### 1. Update Content Security Policy (CSP)
Modify `app/middleware/security.py` to allow the following trusted sources:
*   `style-src`: `https://fonts.googleapis.com` (Google Fonts), `https://cdn.jsdelivr.net/npm/` (Swagger UI CSS)
*   `script-src`: `https://cdn.jsdelivr.net/npm/` (Swagger UI/ReDoc JS)
*   `img-src`: `https://fastapi.tiangolo.com` (Favicon)
*   `font-src`: `https://fonts.gstatic.com` (Google Fonts)

### 2. Verify and Fix CORS/CSRF logic
The backend uses a strict custom CSRF check in `app/main.py`. We need to ensure that the `Origin` header from the frontend is correctly matching the allowed list.
*   **Critical Finding**: The user reported `CORS_ORIGINS` as `https://to-do-4w0k.onrender.com/, https://sajankp.github.io/to-do-frontend/`.
*   **The Issue**: CORS `Origin` headers **never** contain paths (e.g., `/to-do-frontend/`). Browsers only send `https://sajankp.github.io`.
*   **The Fix**: We must update `app/config.py` to strip paths/trailing slashes from configured origins, OR strictly advise the user to correct the env var. We will do both: make the code robust AND advise the user.

## Data Model Changes
None.

## API Changes
*   **Headers**: The `Content-Security-Policy` header will be updated.

## Implementation Plan
1.  **Test (Red)**: Create tests in `app/tests/middleware/test_security_csp.py` asserting that the CSP header contains the required allowed domains.
2.  **Test (Red)**: Add tests to `app/tests/test_cors.py`.
    *   Test that `https://sajankp.github.io` fails validation if the config is set to `https://sajankp.github.io/to-do-frontend/`.
    *   Test that it passes if we implement the fix.
3.  **Implement (Green)**:
    *   Update `app/middleware/security.py` for CSP.
    *   Update `app/config.py`'s `get_cors_origins_list` to strictly parse only the origin part of the URL, ignoring paths.
4.  **Verification**: ensure tests pass.

## Test Strategy
*   **Unit Tests**:
    *   `test_csp_headers`: Request `/` and check `Content-Security-Policy` header structure.
    *   `test_cors_allowed_origin`: Request with `Origin: https://sajankp.github.io` and check response headers.
    *   `test_cors_config_parsing`: specific unit test for `Settings.get_cors_origins_list` to ensure it handles trailing slashes/paths gracefully.

## Open Questions
*   Are there other domains needed for the frontend (e.g. valid analytics)? *Assumption: No, based on error logs provided.*
