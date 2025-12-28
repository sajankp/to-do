# Spec: Gemini API Backend Proxy

## Status
✅ Approved

## Problem Statement

The voice assistant feature currently bundles the Gemini API key directly in the frontend JavaScript bundle. This creates critical security vulnerabilities:

- API key visible in browser DevTools → Sources → bundled JavaScript
- Anyone can extract and abuse the key
- No usage tracking or rate limiting per user
- Potential for significant API cost abuse
- No way to revoke access for specific users

## Proposed Solution

Implement a backend proxy endpoint that handles all Gemini API calls:

```
Frontend → Backend /api/ai/voice → Gemini API
```

The API key stays on the server, never exposed to clients.

## API Changes

### New Endpoints

#### `POST /api/ai/voice`
Synchronous voice processing endpoint.

**Request:**
```json
{
  "prompt": "What tasks do I have due today?",
  "context": {
    "todos": ["...user's todos..."]
  }
}
```

**Response:**
```json
{
  "response": "You have 3 tasks due today...",
  "tokens_used": 150
}
```

**Rate Limit:** 10 requests/minute per user

#### `WebSocket /api/ai/voice/stream`
Streaming responses for real-time voice interaction.

## Data Model Changes

### New Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | (required) |
| `AI_RATE_LIMIT` | Requests per minute per user | `10` |

### Usage Logging (Optional)

```python
class AIUsageLog:
    user_id: str
    endpoint: str
    tokens_used: int
    timestamp: datetime
```

## Implementation Plan

### Backend

1. [ ] Create new router: `app/routers/ai.py`
2. [ ] Add `GEMINI_API_KEY` to config.py
3. [ ] Implement `POST /api/ai/voice` endpoint
4. [ ] Add rate limiting (10 req/min per user)
5. [ ] Implement streaming WebSocket endpoint
6. [ ] Add usage logging
7. [ ] Write unit tests
8. [ ] Write integration tests

### Frontend

1. [ ] Remove `GEMINI_API_KEY` from frontend env
2. [ ] Update VoiceAssistant to call backend endpoint
3. [ ] Handle streaming responses via WebSocket
4. [ ] Add error handling for rate limits

### Cleanup

1. [ ] Remove `process.env.API_KEY` from vite.config.ts
2. [ ] Remove direct Gemini SDK usage from frontend

## Test Strategy

### Unit Tests
- [ ] Endpoint returns valid response
- [ ] Rate limiting triggers at 10 requests
- [ ] Unauthorized requests rejected
- [ ] Invalid prompts handled gracefully

### Integration Tests
- [ ] Full flow: Frontend → Backend → Gemini → Response
- [ ] WebSocket streaming works
- [ ] User isolation (can't see other users' usage)

### Security Tests
- [ ] API key not exposed in any response
- [ ] Rate limiting enforced per user
- [ ] Unauthorized access blocked

## Open Questions

- [ ] Should we cache AI responses for identical prompts?
- [ ] What's the token limit per request?
- [ ] Should we implement a usage quota per user/day?

## Performance Considerations

- **Added latency:** ~50-100ms (one extra hop)
- **Acceptable for voice UX:** Yes, within human perception threshold
- **Streaming mitigates latency:** First tokens arrive quickly

## Trade-offs Accepted

| Trade-off | Accepted Because |
|-----------|------------------|
| Added latency | Security is more important than 50ms |
| Backend complexity | Centralized auth is worth it |
| Stateful WebSocket | Required for streaming, manageable |

## Related

- [ADR-008: Gemini API Backend Proxy](../adr/008-gemini-api-backend-proxy.md)
- [Technical Debt TD-006](../ROADMAP.md)
