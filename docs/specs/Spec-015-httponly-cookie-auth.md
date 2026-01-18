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
cookie_secure: bool = Field(default=True, description="Use Secure flag (HTTPS only)")
cookie_samesite: str = Field(default="lax", description="SameSite policy")
cookie_domain: str = Field(default="", description="Cookie domain")
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

**New `/auth/logout` endpoint:**
- Clear both cookies

**Auth middleware:**
- Read `access_token` from cookie
- Fall back to `Authorization` header for backward compatibility

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

- HttpOnly prevents XSS access to tokens
- Secure flag ensures HTTPS-only transmission
- SameSite=Lax prevents CSRF for non-GET requests
- Explicit domain prevents cross-subdomain leakage
