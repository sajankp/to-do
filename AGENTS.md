# AI Agent Context

> [!CAUTION]
> **PRE-FLIGHT CHECK — READ BEFORE ANY WORK**
>
> Before starting ANY task in this repository, you MUST:
> 1. Read this file (`AGENTS.md`) completely
> 2. Review [.agent/workflows/development-workflow.md](.agent/workflows/development-workflow.md)
> 3. Use the decision flowchart to determine if a Feature Spec is required
>
> **This is not optional.** Skipping this step leads to wasted work and incorrect implementations.

---

**FastTodo** is a production-grade REST API for todo management.
**Stack:** Python 3.13 · FastAPI · MongoDB · Pydantic v2
**Live API:** https://to-do-4w0k.onrender.com/docs

This repository contains the **backend only**. Frontend is in [sajankp/to-do-frontend](https://github.com/sajankp/to-do-frontend).

> For general project information, see [README.md](README.md). For architecture details, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

> ⚠️ **All commands in this document assume the virtual environment is activated:**
> ```bash
> source venv/bin/activate
> ```

> 🚨 **CRITICAL: Spec-Driven Development (SDD) Mandate**
> You MUST follow the [Development Workflow](.agent/workflows/development-workflow.md) for ANY new feature or architectural change.
>
> **The Golden Rule for Agents:**
> 1. **NEVER** write code based solely on an ADR or a user prompt.
> 2. **ALWAYS** verify a Feature Spec exists in `docs/specs/` and is marked `Status: Approved`.
> 3. **IF** Spec is `Planned` or `Draft` → STOP. Ask user to review/approve it first.
> 4. **IF** ADR is `Accepted` but Spec is `Planned` → STOP. The Spec governs validity.
>
> ```
> Workflow: Spec (Approve) → ADR (Approve) → Branch (Confirm) → Implement → Update ARCHITECTURE.md
> ```

> 📋 **Project Context:**
> This is a reference implementation, not a quick prototype.
> Prioritize documentation quality, clean commit history, and thoughtful decision records.

## Quick Start for Agents

### Current Project Status

- ✅ Comprehensive test suite (run `pytest --cov` for current stats)
- ✅ User authentication with JWT (access + refresh tokens)
- ✅ Todo CRUD operations with user isolation
- ✅ Pydantic v2 migration completed
- ✅ **Rate limiting implemented** (IP/User based)

---

## Critical Things to Know

### 1. Authentication Flow
- Auth middleware in `app/main.py` handles token validation for all protected routes
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

### ❌ DON'T (Common Mistakes)
- **DON'T** make changes directly on `main`—always create a branch first, even for docs
- **DON'T** access `user_id` from request body—always use `request.state.user_id`
- **DON'T** skip tests—pre-commit hooks won't catch logic bugs
- **DON'T** modify `ARCHITECTURE.md` without discussion first
- **DON'T** create ADRs before updating `ARCHITECTURE.md`
- **DON'T** hardcode secrets—use environment variables via `app/config.py`

### 🛑 Agent Commit Rules

> [!CAUTION]
> **NEVER commit without explicit user approval**
>
> 1. **Stage changes** and show the user what will be committed
> 2. **Request approval** before running `git commit`
> 3. **Only commit** after receiving explicit "yes", "approved", "proceed", or similar confirmation

### 📝 Agent Documentation Rules

- **Operational guidance** (e.g., "how to configure branch protection in GitHub UI") should be provided **in chat**, not as committed documentation files
- Only commit documentation that is **reference material** users will look up later (e.g., API specs, architecture docs)
- **No obvious comments** — Don't add comments that simply restate what the code does. Comments should explain *why*, not *what*.
- When unsure, ask: "Should I add this as a committed doc or just explain it here?"

> **🔀 Branching Rule:** If you're creating new files, modifying roadmap/architecture, or making more than a trivial typo fix—**create a branch first**. Ask: "Should I create branch `docs/xyz` or `feat/xyz` for this?"

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
| `app/main.py` | App entry, middleware | Auth middleware, lifespan events |
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

### Modules Needing Test Attention
- `app/main.py` - middleware edge cases
- `app/routers/todo.py` - error scenarios
- `app/models/base.py` - serialization edge cases

### Quick Sanity Check
```bash
# Verify everything works after setup or changes
pytest app/tests/ -q && echo "✅ All tests passing"
```

---

## Common Tasks

### Adding a New Endpoint

1. Define Pydantic model in `app/models/`
2. Create route handler in `app/routers/`
3. Add router to `app/main.py` with `app.include_router()`
4. Write tests in `app/tests/routers/`

### Working with MongoDB

```python
# Access collections via request.app
collection = request.app.todo  # or .user

# Always filter by user for isolation
todos = collection.find({"user_id": request.state.user_id})
```

---

## Security Best Practices

- Never log sensitive data (passwords, tokens)
- Always use `request.state.user_id`, never from request body
- Use environment variables via `app/config.py` for secrets

> For full security status and roadmap, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#security-architecture).

---

## Development Workflow

### Local Setup (First Time Only)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pre-commit install
cp .env.example .env  # Edit with your credentials
```

### Running the Server
```bash
uvicorn app.main:app --reload --port 80
```

### Docker Setup
```bash
docker build -t fasttodo .
docker run -p 80:80 --env-file .env fasttodo
```

### Before Committing

Pre-commit hooks run automatically on `git commit`. To run manually:
```bash
pre-commit run --all-files
```

Hooks enforce: Ruff linting, conventional commits, trailing whitespace removal.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Import errors in tests | Ensure `conftest.py` exists, `pytest.ini` has `pythonpath = .` |
| Database connection fails | Check `.env` credentials, MongoDB Atlas IP whitelist |
| Pydantic errors | Use `model_config` not `Config`, `model_dump()` not `dict()` |

---

## Additional Resources

- [README.md](README.md) - Project overview and setup
- [Architecture Spec](docs/ARCHITECTURE.md) - Full system specification
- [Test Plan](docs/test-plan.md) - Testing checklist
- [ADRs](docs/adr/) - Architecture Decision Records
- [Live API](https://to-do-4w0k.onrender.com/docs) - Production Swagger docs
- [GitHub Repository](https://github.com/sajankp/to-do/)
