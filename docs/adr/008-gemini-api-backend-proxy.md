# ADR-008: Gemini API Backend Proxy

## Status

**Accepted** (2025-12-21)

## Context

The voice assistant feature in the FastTodo frontend uses the Gemini AI API. Currently, the implementation bundles the Gemini API key directly in the frontend JavaScript bundle, making it visible in browser DevTools and vulnerable to abuse.

### Problem Statement

- API key visible in browser DevTools → Sources → bundled JavaScript
- Anyone can extract and abuse the key
- No usage tracking or rate limiting per user
- Potential for significant API cost abuse
- No way to revoke access for specific users

## Decision

We will implement a **backend proxy endpoint** for all Gemini API calls.

```
Frontend → Backend /api/ai/voice → Gemini API
```

### Implementation Details

- **New router:** `app/routers/ai.py`
- **Rate limit:** 10 requests/minute per user
- **Endpoints:**
  - `POST /api/ai/voice` - Synchronous voice processing
  - `WebSocket /api/ai/voice/stream` - Streaming responses

## Options Considered

| Option | Description | Pros | Cons | Effort |
|--------|-------------|------|------|--------|
| **A: Backend Proxy (Chosen)** | Frontend → Backend → Gemini | Key secure, user tracking, rate limiting, cost controls | Adds latency, backend complexity | 2 days |
| B: Edge Function | Frontend → Vercel/Netlify Edge → Gemini | Low latency, separate service | Another service to manage, harder auth integration | 1 day |
| C: AI Studio Only | Use `window.aistudio` API only | No key management | Only works in AI Studio, not production | 0 days |

## Consequences

### Positive

- API key never leaves server, eliminating exposure risk
- Per-user rate limiting prevents abuse and controls costs
- Usage logging enables analytics and debugging
- Centralized authentication (uses existing JWT middleware)
- Can inject user context into AI prompts

### Negative

- ~50-100ms additional latency for AI requests (acceptable for voice UX)
- Backend state management for streaming WebSocket connections
- Additional backend complexity and maintenance

### Trade-offs Accepted

- Latency vs Security: Security wins
- Complexity vs Control: Control wins

## Related

- [docs/spec.md](../spec.md) - Full decision context in "Architectural Decisions Summary"
- TD-006 in Technical Debt Registry
