# Spec-015: HttpOnly Cookie Authentication

**Status:** Approved
**Roadmap Items:** TD-011 + TD-015
**Effort:** 2 days (backend portion)

---

## Problem Statement

Tokens stored in localStorage are vulnerable to XSS attacks. This spec migrates authentication to HttpOnly cookies, which cannot be accessed by JavaScript.

## Goals

1. Set `access_token` and `refresh_token` as HttpOnly cookies on login
2. Read tokens from cookies in auth middleware
3. Implement `/auth/logout` endpoint to clear cookies
4. Support "Remember me" to control refresh token cookie

---

## Proposed Changes

### 1. Configuration (`app/config.py`)

Add cookie configuration:

```python
# Cookie settings - designed for cross-origin deployment
# (Frontend on GitHub Pages, Backend on Render)

@property
def cookie_secure(self) -> bool:
    """Always True in production for HTTPS-only cookies."""
    return self.is_production

cookie_samesite: str = Field(
    default="none",
    description="SameSite policy. 'none' required for cross-origin cookies."
)
cookie_domain: str = Field(
    default="",
    description="Cookie domain. Empty = backend origin only."
)
```

> [!IMPORTANT]
> **Cross-Origin Deployment:** Frontend (GitHub Pages) and backend (Render) are on different domains.
> This requires `SameSite=None` for cookies to be sent cross-origin.

---

### 2. CORS Configuration

Update existing CORS settings for cookie support:

```python
# CORS must use explicit origins (not "*") for credentials
cors_origins: str = Field(
    "https://sajankp.github.io",
    description="Comma-separated allowed origins. Cannot be '*' with credentials."
)
cors_allow_credentials: bool = Field(
    True,
    description="Required for cross-origin cookie authentication."
)
```

**Render Environment Variables:**
- `CORS_ORIGINS=https://sajankp.github.io`
- `CORS_ALLOW_CREDENTIALS=true`

---

### 3. Auth Endpoints (`app/main.py`)

**`/token` endpoint:**
- Add `Response` parameter
- Set HttpOnly cookies instead of returning tokens in body
- Accept `remember_me` parameter to control refresh token storage

**`/token/refresh` endpoint:**
- Read `refresh_token` from cookie instead of query param
- Set new `access_token` cookie in response

**New `POST /auth/logout` endpoint:**
- Clear both cookies by setting `Max-Age=0`
- Must use POST method to prevent CSRF attacks

**Auth middleware:**
- Read `access_token` from cookie first
- Fall back to `Authorization` header for backward compatibility

> **Deprecation Note:** The `Authorization` header fallback is for migration only.
> It will be removed in a future release (target: v2.0). Clients should migrate
> to cookie-based auth after this release.

---

## Current Implementation Notes (as of 2026-02-15)

- Login and refresh set/read HttpOnly cookies for `access_token` and `refresh_token`.
- `/auth/logout` is implemented and clears both cookies.
- `remember_me` is not implemented; refresh cookie is always set with standard expiry.
- Auth middleware reads `access_token` from cookies only; `Authorization` header fallback is not implemented.
- `cookie_secure` is forced `True` when `SameSite=None` (required by browsers), regardless of environment.

## Verification Plan

### Automated Tests

Add to `app/tests/test_auth.py` (new file):
- `test_login_sets_httponly_cookies`
- `test_refresh_reads_cookie`
- `test_logout_clears_cookies`
- `test_remember_me_false_no_refresh_cookie`
- `test_cors_allows_credentials`

```bash
make test
```

---

## Security Considerations

### Why HttpOnly Cookies?
HttpOnly cookies cannot be accessed by JavaScript, making them immune to XSS token theft attacks.

### Cookie Attributes

| Attribute | Value | Rationale |
|-----------|-------|-----------|
| **HttpOnly** | `true` | Prevents JavaScript access, mitigating XSS |
| **Secure** | `true` (prod) | Ensures cookies only sent over HTTPS |
| **SameSite** | `None` | Required for cross-origin cookies |
| **Domain** | `""` (empty) | Scopes to backend origin only |

### Why SameSite=None?

> [!WARNING]
> **Cross-Origin Requirement:** With frontend on GitHub Pages and backend on Render (different domains), `SameSite=Lax` would **block** cookie transmission on API requests.

`SameSite=None` allows cookies to be sent cross-origin. This requires:
1. `Secure=true` (mandated by browsers)
2. Explicit CORS origins (not `*`)
3. `credentials: 'include'` on frontend

### CSRF Protection

With `SameSite=None`, we lose some automatic CSRF protection. Mitigations:
1. **CORS:** Only allows requests from `https://sajankp.github.io`
2. **State-changing endpoints:** All use POST/PUT/DELETE (not GET)
3. **Future consideration:** Add CSRF token header if needed

### Future: Same-Origin Deployment
If frontend/backend move to same domain (e.g., custom domain), update:
- `cookie_samesite` to `lax`
- `cookie_domain` to `.yourdomain.com`
