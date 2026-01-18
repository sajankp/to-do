# Spec-004a: Configurable Log Level

**Status:** Approved
**Related Spec:** Spec-004 (Structured Logging)
**Related Issue:** TD-004
**Effort:** 0.5 Day

---

## Problem Statement

The current structured logging implementation (Spec-004) hardcodes the log level to `INFO` in `app/utils/logging.py` (line 88). This creates several operational challenges:

1. **Debugging Difficulty**: Cannot enable `DEBUG` logs in production without code changes and redeployment.
2. **Log Noise**: Cannot reduce log verbosity to `WARNING` or `ERROR` in high-traffic environments.
3. **Environment Mismatch**: Development and production environments should have different default log levels, but currently share the same hardcoded value.
4. **Operational Inflexibility**: DevOps teams cannot adjust logging verbosity via environment variables during incidents.

### Current Implementation Gap

```python
# app/utils/logging.py (line 88)
root_logger.setLevel(logging.INFO)  # ❌ Hardcoded
```

This violates the [12-Factor App](https://12factor.net/config) principle of storing configuration in the environment.

---

## Proposed Solution

Add a `LOG_LEVEL` environment variable that:
1. Accepts standard Python logging levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
2. Normalizes case-insensitive input to uppercase (e.g., `debug` → `DEBUG`)
3. Validates input and rejects invalid values with a clear error message
4. Defaults to `INFO` if not specified
5. Integrates seamlessly with the existing `setup_logging()` function

### Design Principles

- **Fail Fast**: Invalid log levels should raise `ValueError` during application startup (not at runtime)
- **User-Friendly**: Accept case-insensitive input (developers shouldn't need to remember exact casing)
- **Explicit Defaults**: Default to `INFO` (balanced verbosity for most use cases)
- **Backward Compatible**: Existing deployments without `LOG_LEVEL` continue to work with `INFO`

---

## API Changes

### Configuration (`app/config.py`)

Add a new field to the `Settings` class:

```python
# Logging
log_level: str = Field(
    "INFO",
    validation_alias="LOG_LEVEL",
    description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
```

**Validation Requirements:**
- Must normalize to uppercase (via `@field_validator`)
- Must be one of: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- Must raise `ValueError` with message `"Invalid LOG_LEVEL: {value}. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL"` for invalid values

### Environment Variable

**Name:** `LOG_LEVEL`
**Type:** String
**Default:** `INFO`
**Valid Values:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (case-insensitive)
**Example:** `LOG_LEVEL=DEBUG`

### Logging Setup (`app/utils/logging.py`)

Update `setup_logging()` to use the configured log level:

```python
# Before (line 88)
root_logger.setLevel(logging.INFO)

# After
root_logger.setLevel(getattr(logging, settings.log_level))
```

---

## Data Model Changes

None. This is a configuration-only change.

---

## Implementation Plan

### Step 1: Add Field Validator to `Settings`

Add a `@field_validator` for `log_level` in `app/config.py`:

```python
from pydantic import field_validator

@field_validator("log_level", mode="before")
@classmethod
def validate_log_level(cls, value: str) -> str:
    """Validate and normalize log level."""
    if not isinstance(value, str):
        raise ValueError(f"LOG_LEVEL must be a string, got {type(value)}")

    normalized = value.upper()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

    if normalized not in valid_levels:
        raise ValueError(
            f"Invalid LOG_LEVEL: {value}. Must be one of: {', '.join(sorted(valid_levels))}"
        )

    return normalized
```

### Step 2: Update `setup_logging()` Function

Modify `app/utils/logging.py` to use `settings.log_level`:

```python
# Line 88
root_logger.setLevel(getattr(logging, settings.log_level))
```

### Step 3: Update `.env.example`

Add documentation for the new environment variable:

```bash
# Logging Configuration
# Valid values: DEBUG, INFO, WARNING, ERROR, CRITICAL (case-insensitive)
# Default: INFO
LOG_LEVEL=INFO
```

### Step 4: Update Documentation

Update `docs/specs/004-structured-logging.md` to reference this spec in the "Configuration" section.

---

## Test Strategy

### Unit Tests (`app/tests/test_config.py`)

Create a new test class `TestLogLevelConfiguration`:

1. **Valid Uppercase Input**
   - Test: `LOG_LEVEL=DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
   - Assert: `settings.log_level == expected_uppercase_value`

2. **Case Normalization**
   - Test: `LOG_LEVEL=debug`, `info`, `warning`, `error`, `critical` (lowercase)
   - Assert: `settings.log_level == expected_uppercase_value`
   - Test: `LOG_LEVEL=Debug`, `Info`, etc. (mixed case)
   - Assert: `settings.log_level == expected_uppercase_value`

3. **Invalid Input Rejection**
   - Test: `LOG_LEVEL=INVALID`, `TRACE`, `VERBOSE`, `123`, etc.
   - Assert: Raises `ValueError` with message matching `"Invalid LOG_LEVEL"`

4. **Default Value**
   - Test: `LOG_LEVEL` not set
   - Assert: `settings.log_level == "INFO"`

### Integration Tests (`app/tests/test_logging.py`)

1. **Log Level Applied to Root Logger**
   - Test: Set `LOG_LEVEL=DEBUG`, call `setup_logging()`
   - Assert: `logging.getLogger().level == logging.DEBUG`
   - Test: Set `LOG_LEVEL=ERROR`, call `setup_logging()`
   - Assert: `logging.getLogger().level == logging.ERROR`

2. **Logging Output Format (Existing Test)**
   - Verify: Existing `test_logging_output_format` still passes
   - Purpose: Ensure log level changes don't break JSON rendering

### Manual Testing

1. **Local Development**
   - Set `LOG_LEVEL=DEBUG` in `.env`
   - Run `uvicorn app.main:app --reload`
   - Verify: Debug logs appear in console with pretty formatting

2. **Production Simulation**
   - Set `ENVIRONMENT=production` and `LOG_LEVEL=WARNING`
   - Run application
   - Verify: Only WARNING+ logs appear as JSON

---

## Security Considerations

- **No Sensitive Data**: Log levels themselves don't expose sensitive information
- **DoS Risk (Mitigated)**: Setting `LOG_LEVEL=DEBUG` in production could increase log volume, but this is an operational decision (not a security vulnerability)
- **Validation**: Invalid log levels fail at startup (not runtime), preventing misconfiguration

---

## Performance Considerations

- **Negligible Impact**: Log level check is performed once during `setup_logging()` at startup
- **Runtime Efficiency**: Python's logging module handles level filtering efficiently (no performance degradation)

---

## Backward Compatibility

✅ **Fully Backward Compatible**

- Existing deployments without `LOG_LEVEL` will default to `INFO` (current behavior)
- No breaking changes to API or data models

---

## Alternatives Considered

### Alternative 1: Use Python's `logging.getLevelName()`

**Rejected**: `getLevelName()` accepts numeric levels (e.g., `10` for `DEBUG`), which is less user-friendly than string names.

### Alternative 2: Separate Log Levels for Different Modules

**Deferred**: Could add `UVICORN_LOG_LEVEL`, `APP_LOG_LEVEL`, etc., but this adds complexity. Start simple with a single global level.

### Alternative 3: Dynamic Log Level Changes (Runtime API)

**Out of Scope**: Could add an admin endpoint to change log levels at runtime, but this requires authentication and is better suited for a future monitoring feature (TD-005).

---

## Open Questions

None. Implementation is straightforward.

---

## Success Criteria

- [ ] `LOG_LEVEL` environment variable controls application log level
- [ ] Case-insensitive input is normalized to uppercase
- [ ] Invalid log levels raise `ValueError` at startup
- [ ] All tests pass (unit + integration)
- [ ] `.env.example` documents the new variable
- [ ] Spec-004 references this spec

---

## References

- [Python Logging Levels](https://docs.python.org/3/library/logging.html#logging-levels)
- [12-Factor App: Config](https://12factor.net/config)
- [Pydantic Field Validators](https://docs.pydantic.dev/latest/concepts/validators/)
- Spec-004: Structured Logging with Structlog

---

*Spec created: 2026-01-18*
