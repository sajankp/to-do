# ADR-004: JWT-Based Authentication Strategy

**Status:** Accepted

**Date:** 2023 (Initial implementation), Updated 2024

**Deciders:** Project team

**Related PRs:** 
- [#46 - Fix User create endpoint authentication](https://github.com/sajankp/to-do/pull/46)
- [#39 - Fix: Incorrect mechanism to handle login](https://github.com/sajankp/to-do/pull/39)

---

## Context

We needed an authentication mechanism for the API that:

- Works for stateless API (no server-side sessions)
- Scales horizontally without shared session storage
- Supports mobile/web clients equally
- Provides reasonable security
- Simple to implement and test

### Alternatives Considered

1. **Session-Based Authentication**
   - Pros: Familiar pattern, easy to invalidate
   - Cons: Requires session storage (Redis), not scalable, CSRF concerns

2. **OAuth 2.0 (Third-Party)**
   - Pros: Delegated authentication, social login
   - Cons: Complex setup, external dependencies, overkill for MVP

3. **API Keys**
   - Pros: Simple, stateless
   - Cons: No expiration, hard to rotate, security risks

4. **JWT Tokens** ✅
   - Pros: Stateless, self-contained, industry standard, flexible claims
   - Cons: Can't easily invalidate, token size, need rotation strategy

---

## Decision

We implemented **JWT (JSON Web Tokens)** authentication with:
- Access tokens (short-lived, 30 min)
- Refresh tokens (longer-lived, 1 hour)
- HS256 algorithm (HMAC with SHA-256)
-Middleware-based validation

### Implementation Details

#### Token Structure
```python
{
  "sub": "username",      # Subject (username)
  "sub_id": "user_id",    # User MongoDB ObjectId
  "exp": 1234567890       # Expiration timestamp
}
```

#### Endpoints
- `POST /token` - Login, returns access + refresh tokens
- `POST /token/refresh` - Exchange refresh token for new access token
- `POST /user` - User registration (public endpoint)

#### Security Measures
- **Password Hashing**: bcrypt with automatic salt
- **Token Secrets**: Stored in environment variables
- **Middleware**: Automatic validation on protected routes
- **User Isolation**: `user_id` in token, validated on every request

### Key Files
- `app/routers/auth.py` - Token creation, password hashing, validation
- `app/main.py` (lines 53-86) - Authentication middleware
- `app/models/user.py` - User and token schemas

---

## Consequences

### Positive

✅ **Stateless**: No session storage, horizontally scalable  
✅ **Cross-Platform**: Works identically for web/mobile/API clients  
✅ **Standard**: Industry-accepted pattern, many libraries  
✅ **Flexible**: Easy to add claims (roles, permissions)  
✅ **Self-Contained**: All info in token, no DB lookup per request  
✅ **Refresh Strategy**: Short access tokens + refresh tokens balance security/UX  

### Negative

⚠️ **No Revocation**: Can't invalidate tokens before expiry (mitigation: short expiry)  
⚠️ **Token Size**: Larger than session IDs (acceptable for HTTP headers)  
⚠️ **Secret Management**: Leaked SECRET_KEY compromises all tokens  
⚠️ **Clock Skew**: Expiration depends on accurate server time  

### Security Issues Fixed

- **PR #39**: Fixed incorrect login mechanism (authentication bypass)
- **PR #46**: Fixed user creation endpoint allowing unauthorized access
- **Middleware**: Added consistent token validation across all protected routes

### Known Limitations

- **Issue #34**: No rate limiting on auth endpoints (brute force vulnerability - OPEN)
- No token blacklist (logout just discards client-side token)
- Single secret key (can't rotate without invalidating all tokens)
- No refresh token rotation (same refresh token reusable until expiry)

---

## Future Improvements

### Should Implement
1. **Rate Limiting** (Issue #34, HIGH PRIORITY)
   - Prevent brute force attacks on `/token` endpoint
   - Recommended: 5 attempts per IP per minute

2. **Refresh Token Rotation**
   - Issue new refresh token on each use
   - Invalidate old refresh token

3. **Token Blacklist**
   - Store revoked tokens in Redis
   - Check on validation

### Could Consider
- OAuth 2.0 for social login
- Two-factor authentication (2FA)
- JWT asymmetric keys (RS256) for microservices
- Shorter access token expiry (5-15 min)

---

## Verification

- ✅ 18 authentication tests in `app/tests/routers/test_auth.py` (all passing)
- ✅ Middleware tests in `app/tests/test_integration_todo_user.py`
- ✅ Password hashing verified with bcrypt
- ✅ Token expiration enforced
- ✅ User isolation working (can't access other users' todos)

---

## References

- [JWT.io](https://jwt.io/) - JWT standard and debugger
- [RFC 7519](https://tools.ietf.org/html/rfc7519) - JWT specification
- [python-jose](https://python-jose.readthedocs.io/) - JWT library used
- [bcrypt](https://github.com/pyca/bcrypt/) - Password hashing
- [app/routers/auth.py](../../app/routers/auth.py) - Implementation
- [Issue #34](https://github.com/sajankp/to-do/issues/34) - Rate limiting tracking
