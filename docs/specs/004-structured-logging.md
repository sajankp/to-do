# Spec-004: Structured Logging with Structlog

**Status:** Approved
**Related Issue:** TD-004
**Effort:** 1 Day

---

## Problem Statement

Currently, the application uses Python's standard `logging` module with default formatting. This presents several issues in a production environment:
1.  **Parsing Difficulty:** Plain text logs are hard to parse programmatically by log aggregators (like ELK, Datadog, or Grafana Loki).
2.  **Missing Context:** It's difficult to correlate logs across a single request (missing Request IDs) or trace user actions.
3.  **Inconsistent Format:** Third-party libraries (uvicorn, pymongo) have their own logging formats, making the logs messy.

## Proposed Solution

Replace the standard logging configuration with **structlog** to implement structured, JSON-formatted logging.

### Key Features
1.  **JSON Output:** Logs will be output as JSON objects in production.
2.  **Pretty Printing:** Colorful human-readable logs for local development.
3.  **Session Tracking:**
    -   Implement `sid` (Session ID) claim in JWTs.
    -   Log `sid` instead of `user_id` to balance observability with privacy.
4.  **Context Binding:** Bind `request_id`, `sid`, `method`, `path`, and `client_ip` to log entries.

---

## Implementation Plan

### 1. Dependencies
Add `structlog` to `requirements.txt`.

### 2. Auth Updates (`app/routers/auth.py`)
-   Update `create_token` to accept an optional `sid`.
-   If no `sid` is provided (new login), generate a UUID4.
-   Include `sid` in the JWT payload.

### 3. Configuration (`app/utils/logging.py`)
Create a central logging configuration module that:
-   Configures `structlog` processors.
-   Configures standard library logging to sink into structlog.
-   Switches between `ConsoleRenderer` (Dev) and `JSONRenderer` (Prod).

### 4. Middleware (`app/middleware/logging.py`)
Implement `StructlogMiddleware` that:
-   Generates `request_id` (UUID).
-   Extracts `sid` from the JWT (if present).
-   Binds context variables.
-   Logs request start/finish.

### 5. Integration (`app/main.py`)
-   Initialize logging on startup.
-   Add the middleware.

---

## Verification Plan

### Automated Tests
- Verify that the middleware adds `request_id` to response headers.
- Verify that logs are captured and contain expected keys (mocking stdout/stderr).

### Manual Verification
- **Local Dev:** Run `uvicorn`, interact with API, and verify pretty colorful logs in terminal.
- **Production Simulation:** Set `ENV=production`, run app, and verify logs are single-line JSON objects.

---

## Known Limitations

> **Note:** These limitations were discovered in production (2026-01-17) and do not affect core functionality.

### 1. Log Noise from Standard Library Interception
**Symptom:** Production logs contain extra metadata fields:
```json
{
  "_record": "<LogRecord: ...>",
  "_from_structlog": false,
  ...
}
```

**Impact:** Minor - logs are still parseable, but contain unnecessary metadata.

**Cause:** `ProcessorFormatter` adds internal fields when intercepting standard library logs (uvicorn, etc.).

**Workaround:** Filter these fields in log aggregation pipeline (e.g., Datadog, ELK).

**Future Fix:** Implement custom processor to strip these fields before output.

### 2. Duplicate Plain-Text Logs from Uvicorn
**Symptom:** Some uvicorn logs appear as both JSON and plain text:
```
INFO:     Started server process [56]
{"event": "Started server process [56]", ...}
```

**Impact:** Minimal - duplicate entries can be filtered.

**Cause:** Uvicorn's logging is not fully intercepted by `ProcessorFormatter`.

**Future Fix:** Configure uvicorn to use structlog directly or suppress its default handlers.

### 3. Session Tracking Works as Designed ✅
**Verified:** Session IDs (`sid`) are correctly:
- Generated on login
- Included in JWTs
- Extracted by middleware
- Logged with each request
- Maintained across token refreshes

**Example from production:**
```json
{"sid": "0591431d-c39a-4166-a086-9c2633d291da", "path": "/todo/", "method": "GET", ...}
```
