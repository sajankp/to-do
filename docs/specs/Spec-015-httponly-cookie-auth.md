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
# Cookie settings
# Uses existing is_production property from Settings class
cookie_secure: bool = Field(
    default=True,
    description="Use Secure flag (HTTPS only). Override to False for local dev."
)

# Then in middleware/endpoints, use:
# settings.cookie_secure if settings.is_production else False

cookie_samesite: str = Field(default="lax", description="SameSite policy (see Security Considerations)")
cookie_domain: str = Field(
    default="",
    description="Cookie domain. Empty = current host only. Set to '.yourdomain.com' for cross-subdomain sharing."
)
```

---

### 2. Auth Endpoints (`app/main.py`)

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
> to cookie-based auth within 6 months of this release.

---

## Verification Plan

### Automated Tests

Add to `app/tests/test_integration_todo_user.py`:
- `test_login_sets_httponly_cookies`
- `test_refresh_reads_cookie`
- `test_logout_clears_cookies`
- `test_remember_me_false_no_refresh_cookie`

```bash
make test
```

---

## Security Considerations

### Why HttpOnly Cookies?
HttpOnly cookies cannot be accessed by JavaScript, making them immune to XSS token theft attacks. Even if an attacker injects malicious scripts, they cannot read or exfiltrate the authentication tokens.

### Cookie Attributes

| Attribute | Value | Rationale |
|-----------|-------|-----------|
| **HttpOnly** | `true` | Prevents JavaScript access, mitigating XSS |
| **Secure** | `true` (prod) | Ensures cookies only sent over HTTPS |
| **SameSite** | `Lax` | See below |
| **Domain** | `""` (empty) | Scopes to origin host only |

### Why SameSite=Lax over Strict?

- **Strict:** Cookie never sent on cross-site requests, including top-level navigation. This would break links from emails/external sites - users would appear logged out when clicking a link to the app.

- **Lax (chosen):** Cookie sent on top-level `GET` navigation but NOT on cross-site `POST`/`PUT`/`DELETE` requests. This provides CSRF protection for state-changing operations while preserving the expected user experience for navigation.

### Domain Configuration
- Empty domain (default) = cookie scoped to exact origin host only
- Set explicitly (e.g., `.yourdomain.com`) only if frontend/backend are on different subdomains and need to share the cookie
