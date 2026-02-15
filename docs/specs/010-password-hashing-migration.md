# Spec-010: Password Hashing Library Migration

**Status:** ✅ Implemented
**Related ADR:** [ADR-010](../adr/010-password-hashing-library-migration.md)
**Related Issue:** #82

---

## Problem Statement

We are blocked from upgrading `bcrypt` from 4.0.1 to 5.0.0 due to incompatibility with `passlib`, our current password hashing library. This prevents us from:
-Security updates in newer bcrypt versions
- Compatibility with modern Python versions (Python 3.13+ risks)
- Using modern password hashing algorithms

**Root Cause:**
- `passlib` is unmaintained (last release October 2020)
- bcrypt 5.0 removed `__about__` attribute that passlib depends on
- passlib cannot handle bcrypt 5.0's stricter password validation

---

## Proposed Solution

Migrate from `passlib` to `pwdlib` with **Argon2id** as the primary hashing algorithm, while maintaining **backward compatibility** with existing bcrypt hashes.

### Why pwdlib + Argon2id?
- ✅ **Modern security standard**: Argon2id is the 2025 OWASP/NIST recommendation
- ✅ **Active maintenance**: pwdlib is actively developed
- ✅ **Zero user disruption**: Transparent migration without password resets
- ✅ **Better protection**: Resistant to GPU attacks and side-channel analysis

---

## API Changes

**No API changes** — this is purely an internal implementation change. Authentication endpoints remain unchanged.

---

## Data Model Changes

**No schema changes** — the `hashed_password` field in the User model remains a string. The hash format changes transparently:
- Existing: `$2b$12$...` (bcrypt)
- New users: `$argon2id$...` (Argon2id)

---

## Implementation Plan

### Step 1: Update Dependencies

**File:** `requirements.txt`

```diff
-passlib==1.7.4
-bcrypt==4.0.1
+pwdlib[argon2,bcrypt]==0.2.0
```


### Step 2: Update Password Hashing Logic

**File:** `app/routers/auth.py`

**Lines 6, 20** - Replace imports and initialization:
```python
# Before
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# After
from pwdlib import PasswordHash
# Argon2id primary, bcrypt for legacy verification
pwd_hash = PasswordHash.recommended(extra_hashes=["bcrypt"])
```

**Lines 35-40** - Update hash/verify functions:
```python
def hash_password(password: str):
    return pwd_hash.hash(password)  # Now uses Argon2id

def verify_password(plain_password, hashed_password):
    # Supports both Argon2id (new) and bcrypt (legacy)
    is_valid, new_hash = pwd_hash.verify_and_update(plain_password, hashed_password)
    return is_valid, new_hash  # Return both for transparent migration
```

**Lines 54-60** - Update `authenticate_user()` signature:
```python
def authenticate_user(username: str, password: str):
    """Authenticates a user and returns the user object and optional new hash.

    Returns:
        (user, new_hash): User object and new hash if migration needed, or (None, None)
    """
    user = get_user_by_username(username)
    if not user:
        return None, None

    is_valid, new_hash = verify_password(password, user.hashed_password)
    if not is_valid:
        return None, None

    return user, new_hash  # Caller handles hash update
```

> [!CAUTION]
> **Breaking Change**: `authenticate_user()` signature changes from `-> Optional[UserInDB]` to `-> Tuple[Optional[UserInDB], Optional[str]]`. All callers must be updated.

**In `/token` route handler** - Add at top of file:
```python
import logging
import pymongo.errors
```

**In `/token` route handler** - Transparent hash upgrade:
```python
# Authenticate user
user, new_hash = authenticate_user(form_data.username, form_data.password)
if not user:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

# Transparent migration: upgrade old bcrypt hashes to Argon2id
if new_hash:
    try:
        request.app.user.update_one(
            {"username": user.username},
            {"$set": {"hashed_password": new_hash}}
        )
    except pymongo.errors.PyMongoError as e:
        # Log warning but don't fail login
        logging.warning(f"Failed to upgrade password hash for {user.username}: {e}")

# Generate tokens...
```

> [!IMPORTANT]
> **Design Rationale**: Following separation of concerns and project conventions:
> - `authenticate_user()` only authenticates (single responsibility)
> - Route handler orchestrates DB updates using `request.app.user` (established pattern)
> - Top-level imports per PEP 8
> - Specific exception handling (`PyMongoError` not broad `Exception`)

> [!IMPORTANT]
> **Transparent Migration**: When a user with an old bcrypt hash logs in, `verify_and_update()` returns the new Argon2id hash. We immediately update it in the database, migrating active users automatically without password resets.

### Step 3: Update Tests

**File:** `app/tests/routers/test_auth.py`

Update mocked objects:
```diff
-@patch("app.routers.auth.pwd_context.hash")
+@patch("app.routers.auth.pwd_hash.hash")
 def test_hash_password(mock_hash):
     ...

-@patch("app.routers.auth.pwd_context.verify")
-def test_verify_password(mock_verify):
+@patch("app.routers.auth.pwd_hash.verify_and_update")
+def test_verify_password(mock_verify_and_update):
+    mock_verify_and_update.return_value = (True, None)
     ...
```

---

## Test Strategy

### Unit Tests
```bash
# All auth tests
pytest app/tests/routers/test_auth.py -v

# Coverage verification
pytest --cov=app/routers/auth --cov-report=term-missing
```

**Expected:** All 106 tests pass, coverage remains ≥85%

### Integration Testing

1. **New User Registration**
   - Create user → verify hash starts with `$argon2id$`
   - Login → verify token generated correctly

2. **Existing User Login** (bcrypt hash)
   - Login with existing bcrypt-hashed password
   - Verify authentication succeeds
   - Verify token generated correctly

3. **Manual Hash Verification**
   ```python
   from pwdlib import PasswordHash
   pwd_hash = PasswordHash.recommended(extra_hashes=["bcrypt"])

   # Test new Argon2id hash
   new_hash = pwd_hash.hash("test123")
   assert new_hash.startswith("$argon2id$")

   # Test old bcrypt hash verification
   old_hash = "$2b$12$..."  # From existing DB
   is_valid, _ = pwd_hash.verify_and_update("password", old_hash)
   assert is_valid
   ```

---

## Migration Safety

### Zero-Disruption Guarantees
1. ✅ Existing bcrypt hashes continue to work
2. ✅ No password resets required
3. ✅ No database migrations needed
4. ✅ No API contract changes
5. ✅ Fully backward compatible

### Rollback Plan
If issues arise:
1. Revert to `passlib==1.7.4` and `bcrypt==4.0.1`
2. All passwords remain functional (no data changes)
3. Can roll back without user impact

## Migration Timeline

### Immediate (Day 1)
- Deploy updated authentication code
- New users get Argon2id hashes
- Old users can still log in (bcrypt works)

### Gradual (Weeks 1-12)
- Active users automatically migrate to Argon2id on login
- Monitor migration progress via database queries:
  ```javascript
  // Count bcrypt vs Argon2id hashes
  db.user.countDocuments({"hashed_password": {$regex: /^\$2b\$/}})  // bcrypt
  db.user.countDocuments({"hashed_password": {$regex: /^\$argon2id\$/}})  // Argon2id
  ```

### Long-term (After 6-12 months)
- Assess if bcrypt support can be removed
- Inactive users may still have bcrypt hashes (acceptable)
- Can optionally force password reset for completely inactive accounts

---

## Open Questions

None — comprehensive research completed, implementation well-defined.

---
