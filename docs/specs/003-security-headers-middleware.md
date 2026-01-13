# Spec-003: Security Headers Middleware

## Status
✅ Implemented

## Problem Statement
The application currently lacks standard security headers, making it vulnerable to common web attacks including clickjacking, XSS (Cross-Site Scripting), and MIME sniffing.

## Proposed Solution
Implement a middleware in the FastAPI application that injects recommended OWASP security headers into every HTTP response.

## API Changes
No functional API changes. All responses will include additional HTTP headers.

## Data Model Changes
None.

## Implementation Plan
1. Create `SecurityHeadersMiddleware` in `app/middleware/security.py` (or `main.py`).
2. Configure the following headers:
   - `X-Frame-Options: DENY`
   - `X-Content-Type-Options: nosniff`
   - `X-XSS-Protection: 1; mode=block`
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains` (HSTS)
   - `Content-Security-Policy: default-src 'self'` (CSP)
   - `Referrer-Policy: strict-origin-when-cross-origin`
3. Add tests to verify headers are present.

## Test Strategy
- **Unit/Integration Tests**: Make requests to existing endpoints and assert the presence of new headers in the response.

## Open Questions
- Should we use a library like `secure` or implement manually? (Manual is simple enough for this set).
- CSP string needs to be carefully tuned for frontend functionality (WebSocket, etc).

## Related
- [Technical Debt TD-003](../ROADMAP.md)
