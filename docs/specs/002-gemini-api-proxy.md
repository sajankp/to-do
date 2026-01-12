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
Streaming responses for real-time voice interaction using Google Gemini Live API.

**Configuration:**
- **Model:** `gemini-2.5-flash-native-audio-latest`
- **Audio Format:** 16kHz PCM (input/output)
- **Protocol:** JSON over WebSocket

**Connection Flow:**
1. **Connect:** `ws://host/api/ai/voice/stream`
2. **Auth:** Client sends `{"type": "auth", "token": "JWT"}`
3. **Stream:** Bidirectional JSON messages

**Client Messages:**
```json
// Send Audio
{ "type": "audio", "data": "<base64_encoded_pcm_bytes>" }

// End Turn
{ "type": "end_turn" }

// Update Context (Todos)
{ "type": "todos_update", "todos": [...] }
```

**Server Messages:**
```json
// Audio Chunk
{ "type": "audio", "data": "<base64_encoded_pcm_bytes>" }

// Turn Complete
{ "type": "turn_complete" }

// Interrupted
{ "type": "interrupted" }

// Tool Execution (Client Action Required)
{
  "type": "action",
  "action": "create_todo",
  "data": { "title": "...", ... }
}
```

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

### Supported Tools
The backend defines the following tools for the Gemini model:
- `get_todos`: List current tasks
- `create_todo`: Add a new task
- `update_todo`: Edit a task by fuzzy title match
- `delete_todo`: Remove a task by fuzzy title match

## Implementation Plan

### Backend

1. [x] Create new router: `app/routers/ai.py` (and `ai_stream.py`)
2. [x] Add `GEMINI_API_KEY` to config.py
3. [x] Implement `POST /api/ai/voice` endpoint
4. [x] Add rate limiting (10 req/min per user)
5. [x] Implement streaming WebSocket endpoint
6. [ ] Add usage logging (Deferred)
7. [x] Write unit tests
8. [x] Write integration tests (WebSocket tests)

### Frontend

1. [x] Remove `GEMINI_API_KEY` from frontend env
2. [x] Update VoiceAssistant to call backend endpoint
3. [x] Handle streaming responses via WebSocket
4. [x] Add error handling for rate limits

### Cleanup

1. [x] Remove `process.env.API_KEY` from vite.config.ts
2. [x] Remove direct Gemini SDK usage from frontend

## Test Strategy

### Unit Tests
- [x] Endpoint returns valid response
- [x] Rate limiting triggers at 10 requests
- [x] Unauthorized requests rejected
- [x] Invalid prompts handled gracefully

### Integration Tests
- [x] Full flow: Frontend → Backend → Gemini → Response (Verified manually)
- [x] WebSocket streaming works
- [x] User isolation (can't see other users' usage)

### Security Tests
- [x] API key not exposed in any response
- [x] Rate limiting enforced per user
- [x] Unauthorized access blocked

## Open Questions

- [x] Should we cache AI responses for identical prompts? -> No, conversations are dynamic.
- [x] What's the token limit per request? -> Governed by Gemini model limits.
- [x] Should we implement a usage quota per user/day? -> Implemented rate limit (10/min).

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
