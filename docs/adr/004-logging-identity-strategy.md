# ADR-004: Logging Identity Strategy

**Status:** Accepted
**Date:** 2026-01-15
**Context:** Spec-004 (Structured Logging)

---

## Context
We are implementing structured logging to improve observability. A key requirement is to correlate log entries associated with a specific user session to debug issues effectively.

However, logging the immutable database `user_id` (e.g., `507f1f77bcf86cd799439011`) into plain-text application logs creates a permanent record of a user's activity that is:
1.  **Hard to Anonymize:** Once written to immutable log storage (e.g., CloudWatch, Datadog), it cannot be easily scrubbed if a user requests "Right to be Forgotten" (GDPR).
2.  **Privacy Risk:** If logs are leaked, the entire history of a specific user is exposed.

## Options Considered

### 1. Log `user_id` Directly
-   **Pros:** Simplest to implement. Easiest for debugging historical issues.
-   **Cons:** High privacy risk. violates "Privacy by Design" principles. Hard to satisfy GDPR deletion requests.

### 2. Log Only `request_id`
-   **Pros:** Maximum privacy. No trace of user identity in logs.
-   **Cons:** Poor observability. Cannot easily see "all actions taken by this user in this session". Debugging requires user to provide specific Request IDs.

### 3. Log Ephemeral `sid` (Session ID)
-   **Pros:**
    -   **Good Observability:** Can correlate all logs within a single login session.
    -   **Privacy Preserving:** IDs change on every login. No permanent history linkable to a person without the database state.
    -   **Standard Compliant:** Uses standard OIDC `sid` claim.
-   **Cons:** Requires generating and tracking a new ID in the auth flow.

## Decision
We will use **Option 3: Log Ephemeral `sid` (Session ID)**.

We will strictly avoid logging PII or immutable `user_id` in general application logs.
The `sid` will be a UUIDv4 generated at login and embedded in the JWT (Access & Refresh tokens).

## Consequences
-   **Auth Update:** We must update the `/token` endpoint to generate a UUID and include it as a `sid` claim.
-   **Debugging:** Support teams cannot search logs by `user_id` directly. They must inspect the user's current active session or rely on the user providing a Request ID from a specific error.
-   **Audit Logs:** Critical security events (login, password change) may still record `user_id`, but these will be routed to a separate, secure Audit Log stream, not the general application logs.
