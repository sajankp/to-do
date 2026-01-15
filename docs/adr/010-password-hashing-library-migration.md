# ADR-010: Migrate from passlib to pwdlib for Password Hashing

## Status
Accepted

## Context

We are currently blocked from upgrading bcrypt from 4.0.1 to 5.0.0 (issue #82) due to incompatibility with our password hashing library, passlib.

### Current State
- Using `passlib==1.7.4` with `bcrypt==4.0.1` for password hashing
- passlib provides a `CryptContext` wrapper around bcrypt for password hash/verify operations
- Implementation in `app/routers/auth.py`: `hash_password()` and `verify_password()`

### Problem
1. **passlib is unmaintained**: Last release was October 2020, no active development
2. **bcrypt 5.0 incompatibility**: passlib cannot work with bcrypt 5.x due to:
   - Removed `__about__` attribute that passlib depends on
   - Changed password length validation (72-byte limit enforcement)
3. **Future Python compatibility risks**: passlib may not work with Python 3.13+

### Security Context
Password hashing is a **critical security component**. The choice of algorithm and library affects:
- Protection against brute-force attacks
- Resistance to GPU-based attacks
- Side-channel attack resistance
- Long-term security as computing power increases

## Decision

We will **migrate from passlib to pwdlib** with **Argon2id as the primary hashing algorithm**, while maintaining **backward compatibility with existing bcrypt hashes**.

**Migration approach**: Zero-disruption transparent migration where:
- Existing bcrypt hashes continue to work for login verification
- New passwords use Argon2id
- **Old passwords automatically upgrade to Argon2id on successful login** (transparent rehashing)

This ensures active users gradually migrate to the more secure algorithm without any password resets or user disruption.

> [!NOTE]
> Implementation details are documented in [Spec-010: Password Hashing Migration](../specs/010-password-hashing-migration.md)

## Alternatives Considered

### Option 1: Stay on bcrypt 4.0.1 + passlib (Rejected)
**Pros:**
- No code changes required
- Works with current implementation

**Cons:**
- passlib is abandoned (6+ years without updates)
- Cannot fix security vulnerabilities
- Risk of Python 3.13+ incompatibility
- Stuck on old bcrypt version
- No path forward for modern algorithms

**Verdict:** ❌ Not viable long-term

---

### Option 2: Direct bcrypt library usage (Rejected)
**Pros:**
- Actively maintained bcrypt library
- Can upgrade to bcrypt 5.0
- Simple, focused library

**Cons:**
- bcrypt is aging (winner of Password Hashing Competition was in 2015)
- Argon2 is now recommended by OWASP and security standards
- Would require another migration for Argon2 in the future
- More vulnerable to GPU attacks than Argon2

**Verdict:** ❌ Fixes immediate problem but not forward-looking

---

### Option 3: pwdlib with bcrypt only (Rejected)
**Pros:**
- Modern library (actively maintained)
- Can use bcrypt 5.0
- Easy migration from passlib

**Cons:**
- Doesn't leverage modern Argon2id algorithm
- Less resistant to GPU attacks
- Not aligned with 2025+ security standards

**Verdict:** ❌ Doesn't take advantage of modern security

---

### Option 4: pwdlib with Argon2id + bcrypt backward compat (Selected) ✅
**Pros:**
- **Modern security**: Argon2id is 2025 industry standard (Password Hashing Competition winner)
- **GPU resistance**: Better protection against hardware-accelerated attacks
- **Active maintenance**: pwdlib actively developed, Argon2 widely supported
- **Zero user disruption**: Existing bcrypt hashes work transparently
- **Smooth migration**: Auto-rehash on login (optional enhancement)
- **Future-proof**: Aligned with OWASP and NIST recommendations

**Cons:**
- Slight complexity: Supporting two algorithms during transition
- Dependency change: Need argon2-cffi library (via pwdlib extras)

**Verdict:** ✅ **Best balance of security, compatibility, and future-proofing**

## Consequences

### Positive
- **Enhanced Security**: Argon2id provides better protection against modern attacks
- **Active Maintenance**: pwdlib is maintained, reducing future compatibility risks
- **Unblocks bcrypt upgrade**: Can now upgrade to bcrypt 5.0+ when needed
- **Zero Password Resets**: Users experience no disruption
- **Transparent Hash Upgrade**: Active users automatically migrate to Argon2id on login
- **Industry Standard**: Aligned with 2025 OWASP/NIST recommendations
- **Future-Proof**: Modern algorithm choice reduces need for future migrations
- **Complete Migration Path**: Can eventually remove bcrypt dependency entirely

### Negative / Trade-offs
- **Two Algorithms in Transition**: Temporarily supporting both Argon2id and bcrypt
  - *Mitigation*: This is intentional for backward compatibility, not a problem
- **Dependency Change**: From passlib to pwdlib + argon2-cffi
  - *Mitigation*: Well-maintained, widely-used libraries
- **Learning Curve**: Team needs to understand pwdlib API
  - *Mitigation*: API is simpler than passlib (`verify_and_update()` handles everything)

### Backward Compatibility
- ✅ All existing bcrypt password hashes remain valid
- ✅ Users can log in immediately after deployment
- ✅ No database schema changes required
- ✅ `verify_and_update()` handles format detection automatically

### Testing Requirements
1. Unit tests: Update mocks from `pwd_context` to `pwd_hash`
2. Integration tests: Verify old bcrypt hashes work
3. Manual test: Create new user → verify Argon2id hash format
4. Coverage verification: Maintain 85%+ coverage

## References

- [pwdlib documentation](https://frankie567.github.io/pwdlib/)
- [Argon2 - Wikipedia](https://en.wikipedia.org/wiki/Argon2)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [Password Hashing Competition](https://en.wikipedia.org/wiki/Password_Hashing_Competition)
- [Issue #82: Blocked bcrypt upgrade](https://github.com/sajankp/to-do/issues/82)
