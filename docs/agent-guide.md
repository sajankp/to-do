# Agent Development Guide

> **Note:** This guide is specifically for AI agents or developers new to the FastTodo codebase. For general project information, see the main [README.md](../Readme.md).

---

## Quick Start for Agents

### Current Project Status (as of 2025-11-23)

- ✅ **All 70 tests passing** with 81.10% coverage
- ✅ User authentication with JWT (access + refresh tokens)
- ✅ Todo CRUD operations with user isolation
- ✅ Pydantic v2 migration completed
- ⚠️ **Rate limiting NOT implemented** (critical security gap)

### Immediate Priorities

1. **Rate limiting** - Prevent brute force attacks (HIGH PRIORITY)
2. **Security headers middleware** - OWASP best practices
3. **Repository pattern** - Better code organization
4. **Structured logging** - Production readiness

---

## Critical Things to Know

### 1. Authentication Flow
- Middleware in `app/main.py` handles all auth (lines 53-86)
- User info stored in `request.state.user_id` and `request.state.username`
- Always filter data by `request.state.user_id` to enforce user isolation

### 2. Module Imports
- Project uses absolute imports: `from app.module import ...`
- `conftest.py` adds project root to Python path for tests
- `pytest.ini` has `pythonpath = .` configuration

### 3. Pydantic v2 Patterns
- Use `model_config = ConfigDict(...)` instead of `Config` class
- `PyObjectId` custom type in `app/models/base.py` for MongoDB ObjectId handling
- Settings use `pydantic_settings.BaseSettings`

### 4. Database Access
```python
# In route handlers, access MongoDB via request.app
todos_collection = request.app.todo
users_collection = request.app.user
```

### 5. JWT Token Lifetimes
- Access tokens: 1800 seconds (30 minutes)
- Refresh tokens: 3600 seconds (1 hour)
- Configured via environment variables

---

## Code Architecture

### Directory Structure
```
app/
├── main.py              # FastAPI app, middleware, token endpoints
├── config.py            # Pydantic settings management
├── database/
│   └── mongodb.py       # MongoDB client setup
├── models/              # Pydantic v2 models
│   ├── base.py          # PyObjectId, base model
│   ├── todo.py          # Todo schemas
│   └── user.py          # User schemas
├── routers/             # API endpoints
│   ├── auth.py          # JWT, password hashing, auth logic
│   ├── todo.py          # Todo CRUD operations
│   └── user.py          # User management
└── utils/
    ├── constants.py     # Error messages, constants
    ├── health.py        # Health check utilities
    └── validate_env.py  # Environment validation
```

### Key Files to Understand

| File | Purpose | Important Notes |
|------|---------|-----------------|
| `app/main.py` | App entry, middleware | Auth middleware on lines 53-86 |
| `app/routers/auth.py` | Authentication | Password hashing, JWT creation |
| `app/models/base.py` | PyObjectId type | MongoDB ObjectId handling |
| `conftest.py` | Test configuration | Adds project root to path |

---

## Testing

### Running Tests
```bash
# All tests
pytest app/tests/

# With coverage
pytest --cov=app --cov-report=term-missing

# Specific category
pytest app/tests/routers/test_auth.py -v
```

### Test Structure
- Tests use absolute imports: `from app.main import ...`
- All test directories have `__init__.py` files
- Mock MongoDB operations in tests (no real DB connections)

### Current Coverage: 81.10%

Modules with lower coverage needing attention:
- `app/main.py`: 64.36% (middleware edge cases)
- `app/routers/todo.py`: 66.67% (error scenarios)
- `app/models/base.py`: 64.86% (serialization edge cases)

---

## Common Tasks

### Adding a New Endpoint

1. Define Pydantic model in `app/models/`
2. Create route handler in `app/routers/`
3. Add router to `app/main.py` with `app.include_router()`
4. Write tests in `app/tests/routers/`
5. Ensure route requires authentication (middleware handles this automatically unless excluded)

### Adding Environment Variables

1. Add to `.env.example`
2. Update `app/config.py` Settings class
3. Add validation in `app/utils/validate_env.py` if needed
4. Update documentation

### Working with MongoDB

```python
# Access in routes
collection = request.app.todo  # or .user

# Insert
result = collection.insert_one(data.model_dump())

# Find with user isolation
todos = collection.find({"user_id": request.state.user_id})

# Use PyObjectId for ID fields
from app.models.base import PyObjectId
todo_id = PyObjectId(id_string)
```

---

## Security Considerations

### ✅ Implemented
- JWT token authentication
- Bcrypt password hashing
- User data isolation
- Environment-based secrets
- Docker non-root user

### ⚠️ Missing (High Priority)
- **Rate limiting** on auth endpoints
- Security headers (HSTS, CSP, etc.)
- Request size limits
- IP-based blocking

### Best Practices
- Never log sensitive data (passwords, tokens)
- Always validate user_id from `request.state`, never from request body
- Use type hints for all functions
- Follow principle of least privilege

---

## Development Workflow

### Local Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your credentials
uvicorn app.main:app --reload --port 80
```

### Docker Setup
```bash
docker build -t fasttodo .
docker run -p 80:80 --env-file .env fasttodo
```

### Before Committing
```bash
# Run tests
pytest app/tests/

# Check coverage
pytest --cov=app --cov-report=term-missing

# Verify formatting (if using black/ruff)
# Add linter commands here
```

---

## API Documentation

When app is running, access interactive docs at:
- Swagger UI: http://localhost/docs
- ReDoc: http://localhost/redoc

---

## Troubleshooting

### Import Errors in Tests
- Ensure `conftest.py` exists at project root
- Check `pytest.ini` has `pythonpath = .`
- Verify all test directories have `__init__.py`

### Database Connection Issues
- Check `.env` file has correct MongoDB credentials
- Verify MongoDB Atlas IP whitelist includes your IP
- Check `MONGO_TIMEOUT` setting (default: 5 seconds)

### Pydantic Validation Errors
- Ensure using Pydantic v2 syntax (`model_config`, not `Config`)
- Check `pydantic-settings` is installed
- Use `model_dump()` instead of `dict()`

---

## Performance Notes

### Current Metrics
- API Response Time: <200ms average
- Database Query Time: <50ms average
- Test Suite: 70 tests in ~1.25 seconds

### Optimization Opportunities
- Add database indexes (priority, due_date, user_id)
- Implement Redis caching for frequent queries
- Use Motor for async MongoDB operations
- Add connection pooling configuration

---

## Additional Resources

- [Main README](../Readme.md) - Project overview and setup
- [Test Plan](test-plan.md) - Comprehensive testing checklist
- [Live API](https://to-do-4w0k.onrender.com/docs) - Production deployment
- [GitHub Repository](https://github.com/sajankp/to-do/)
