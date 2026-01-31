from prometheus_client import Counter, Histogram

# User Metrics
LOGINS_TOTAL = Counter("fasttodo_logins_total", "Total login attempts", ["status"])
REGISTRATIONS_TOTAL = Counter("fasttodo_registrations_total", "New user registrations")

# Todo Metrics
TODOS_CREATED_TOTAL = Counter("fasttodo_todos_created_total", "Total todos created")
TODOS_COMPLETED_TOTAL = Counter("fasttodo_todos_completed_total", "Total todos marked complete")
TODOS_DELETED_TOTAL = Counter("fasttodo_todos_deleted_total", "Total todos deleted")

# AI Voice Assistant Metrics
AI_REQUESTS_TOTAL = Counter("fasttodo_ai_requests_total", "AI API calls", ["status"])
AI_TOKENS_USED_TOTAL = Counter("fasttodo_ai_tokens_used_total", "Token consumption", ["type"])
AI_LATENCY_SECONDS = Histogram("fasttodo_ai_latency_seconds", "AI response time")
AI_ERRORS_TOTAL = Counter("fasttodo_ai_errors_total", "AI failures by type", ["error_type"])
