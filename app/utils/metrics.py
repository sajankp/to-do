from prometheus_client import Counter, Gauge, Histogram

# User Metrics
LOGINS_TOTAL = Counter("fasttodo_logins_total", "Total login attempts", ["status"])
REGISTRATIONS_TOTAL = Counter("fasttodo_registrations_total", "New user registrations")

# Todo Metrics
TODOS_CREATED_TOTAL = Counter("fasttodo_todos_created_total", "Total todos created")
TODOS_COMPLETED_TOTAL = Counter("fasttodo_todos_completed_total", "Total todos marked complete")
TODOS_DELETED_TOTAL = Counter("fasttodo_todos_deleted_total", "Total todos deleted")
TODOS_PER_USER = Histogram(
    "fasttodo_todos_per_user",
    "Distribution of todos per user",
    buckets=[0, 1, 5, 10, 25, 50, 100, 250, 500],
)

# AI Voice Assistant Metrics
AI_REQUESTS_TOTAL = Counter("fasttodo_ai_requests_total", "AI API calls", ["status"])
AI_TOKENS_USED_TOTAL = Counter("fasttodo_ai_tokens_used_total", "Token consumption", ["type"])
AI_LATENCY_SECONDS = Histogram("fasttodo_ai_latency_seconds", "AI response time")
AI_ERRORS_TOTAL = Counter("fasttodo_ai_errors_total", "AI failures by type", ["error_type"])

# Database Health Metrics
DB_CONNECTIONS_ACTIVE = Gauge("fasttodo_db_connections_active", "Active MongoDB connections")
DB_QUERY_DURATION_SECONDS = Histogram(
    "fasttodo_db_query_duration_seconds",
    "DB query latency",
    ["operation"],
)
