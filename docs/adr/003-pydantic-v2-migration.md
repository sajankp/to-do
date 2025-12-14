# ADR-003: Migrate to Pydantic v2

**Status:** Accepted

**Date:** November 2024

**Deciders:** Project team

**Related PR:** [#54 - Update python version supported to 3.13 and pydantic from v1 to v2](https://github.com/sajankp/to-do/pull/54)

---

## Context

Pydantic v2 was released with significant performance improvements and new features. Our project was on Pydantic v1 (1.10.13), which was approaching end-of-life.

### Migration Drivers

1. **Performance**: Pydantic v2 is 5-50x faster due to Rust-based core (`pydantic-core`)
2. **Python 3.13 Support**: Wanted to upgrade to latest Python version
3. **Modern Features**: Better validation, improved serialization, enhanced type support
4. **Long-term Support**: v1 reaching EOL, v2 is the future
5. **Breaking Changes**: Required careful migration of existing code

### Alternatives Considered

1. **Stay on Pydantic v1**
   - Pros: No migration effort, working code
   - Cons: Performance penalties, missing features, eventual EOL

2. **Migrate to Pydantic v2** ✅
   - Pros: Better performance, modern features, long-term support
   - Cons: Breaking changes, migration effort, potential bugs

3. **Switch to dataclasses or attrs**
   - Pros: Standard library, simpler
   - Cons: Less validation, no FastAPI integration

---

## Decision

We **migrated to Pydantic v2.12.4** from v1.10.13 as part of PR #54.

### Migration Changes

#### 1. Model Configuration
**Before (v1):**
```python
class MyModel(BaseModel):
    class Config:
        orm_mode = True
```

**After (v2):**
```python
class MyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
```

#### 2. Serialization
**Before (v1):**
```python
model.dict()
model.json()
```

**After (v2):**
```python
model.model_dump()
model.model_dump_json()
```

#### 3. Settings Management
**Before (v1):**
```python
from pydantic import BaseSettings
```

**After (v2):**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
```

#### 4. Field Validators
- Updated to use `@field_validator` decorator
- Changed validation signature patterns
- Improved type hints

### Files Modified

- `app/models/base.py` - Updated BaseModel configurations
- `app/models/todo.py` - Updated validators, ConfigDict
- `app/models/user.py` - Updated  model patterns
- `app/config.py` - Migrated to `pydantic_settings`
- `requirements.txt` - Updated dependencies
- All test files - Updated serialization calls

---

## Consequences

### Positive

✅ **Performance Boost**: 5-50x faster validation (measured in benchmarks)
✅ **Python 3.13 Ready**: Compatible with latest Python version
✅ **Better Error Messages**: More informative validation errors
✅ **Improved Type Support**: Better generic types, stricter validation
✅ **Modern Patterns**: Cleaner code with ConfigDict
✅ **Long-term Viability**: Active development and support

### Negative

⚠️ **Breaking Changes**: Required updates across entire codebase
⚠️ **Learning Curve**: Team needed to learn new patterns
⚠️ **Dependency Update**: Required `pydantic-settings` as separate package
⚠️ **Test Updates**: All tests using `.dict()` needed updates

### Challenges Encountered

1. **Import Changes**: `BaseSettings` moved to separate package
2. **Config Syntax**: `Config` class → `model_config` dict
3. **Serialization**: Method names changed (`.dict()` → `.model_dump()`)
4. **Validator Decorators**: Signature changes required careful review

---

## Verification

- ✅ All 70 tests passing after migration
- ✅ Coverage maintained at 81.10%
- ✅ No runtime errors in production deployment
- ✅ FastAPI integration working seamlessly
- ✅ MongoDB serialization/deserialization functional

---

## Follow-up Actions

- Stay on latest Pydantic v2 minor versions for security/performance
- Monitor breaking changes in future v2.x releases
- Consider migrating to async validation if needed
- Update team documentation with v2 patterns

---

## References

- [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [Pydantic v2 Performance Benchmarks](https://docs.pydantic.dev/latest/why/)
- [PR #54](https://github.com/sajankp/to-do/pull/54) - Migration implementation
- [pydantic-core (Rust)](https://github.com/pydantic/pydantic-core)
- Current version: `pydantic==2.12.4`, `pydantic_settings==2.11.0`
