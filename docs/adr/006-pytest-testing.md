# ADR-006: Pytest with Coverage for Testing

**Status:** Accepted

**Date:** 2024

**Deciders:** Project team

---

## Context

We needed a testing framework that:
- Supports FastAPI async code
- Provides code coverage metrics
- Integrates with CI/CD pipelines
- Has good IDE support
- Allows fixture-based test organization

### Alternatives Considered

1. **unittest (Standard Library)**
   - Pros: Built-in, no dependencies
   - Cons: Verbose, no async support, limited plugins

2. **nose2**
   - Pros: Extension of unittest
   - Cons: Less active development, smaller ecosystem

3. **pytest** ✅
   - Pros: Concise syntax, fixtures, plugins, async support, widely adopted
   - Cons: Not in standard library

4. **pytest + pytest-cov** ✅
   - Pros: Integrated coverage, branch coverage, CI reports
   - Cons: Additional dependency

---

## Decision

We chose **pytest** with **pytest-cov** for testing and **pytest-asyncio** for async support.

### Configuration

#### pytest.ini
```ini
[pytest]
pythonpath = .  # Critical: Adds project root to path
addopts = --cov=app/ --cov-report=term --cov-branch --cov-config=.coveragerc
python_files = app/tests/test_*.py
norecursedirs = .git __pycache__ env build venv .tox
```

#### .coveragerc
```ini
[run]
branch = True
omit = */__init__.py, */tests/*

[report]
show_missing = true
precision = 2
exclude_lines = pragma: no cover, def __repr__, if __name__ == .__main__.:
```

#### conftest.py (Critical Addition)
```python
import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
```

### Test Structure

```
app/tests/
├── __init__.py                    # Package marker
├── test_main.py                   # App-level tests
├── test_integration_todo_user.py  # Integration tests
├── database/
│   ├── __init__.py
│   └── test_mongodb.py
├── models/
│   ├── __init__.py
│   └── test_todo_model.py
├── routers/
│   ├── __init__.py
│   ├── test_auth.py
│   └── test_todo_routes.py
└── utils/
    ├── __init__.py
    └── test_health.py
```

---

## Consequences

### Positive

✅ **Comprehensive Coverage**: 81.10% (exceeding 80% target)  
✅ **Fast Execution**: 70 tests in ~1.25 seconds  
✅ **CI Integration**: GitHub Actions runs automatically  
✅ **Clear Reports**: Term output + HTML reports available  
✅ **Fixtures**: Reusable test setup (mocks, test data)  
✅ **Async Support**: Works seamlessly with FastAPI TestClient  

### Testing Strategy

#### Test Categories
- **Unit Tests**: Models, utilities, individual functions
- **Integration Tests**: User-todo association, middleware, workflows
- **Security Tests**: Authentication, token validation, user isolation
- **Database Tests**: MongoDB operations, connection handling

#### Coverage by Module (Current)
| Module | Coverage |
|--------|----------|
| `app/routers/auth.py` | 100% |
| `app/utils/health.py` | 100% |
| `app/utils/constants.py` | 100% |
| `app/config.py` | 100% |
| `app/models/todo.py` | 91.07% |
| `app/models/user.py` | 88.89% |
| Overall | **81.10%** |

---

## Testing Tools & Libraries

### Core
- `pytest==7.4.4` - Test framework
- `pytest-asyncio==0.23.3` - Async test support
- `pytest-cov==4.1.0` - Coverage plugin

### Testing Utilities
- `httpx==0.26.0` - FastAPI TestClient backend
- Mocking: Built-in `unittest.mock`

### Commands
```bash
# Run all tests with coverage
pytest app/tests/

# Specific test file
pytest app/tests/routers/test_auth.py -v

# HTML coverage report
pytest --cov=app --cov-report=html

# Collection only (no execution)
pytest --collect-only app/tests/
```

---

## Future Improvements

### Should Implement
1. **Increase Coverage to 85%+**
   - Focus on `app/routers/todo.py` (66.67%)
   - Focus on `app/main.py` (64.36%)

2. **Performance Testing**
   - Add `pytest-benchmark` for API response times
   - Load testing with locust or similar

3. **Contract Testing**
   - Validate API contracts with pact
   - Ensure backward compatibility

### Could Consider
- Mutation testing with `mutpy` or `cosmic-ray`
- Property-based testing with `hypothesis`
- Snapshot testing for API responses
- Parallel test execution with `pytest-xdist`

---

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run tests with coverage
  run: pytest
```

Current `.github/workflows/ci.yml` runs tests on:
- Push to `main`
- Pull requests to `main`

Environment variables injected from GitHub Secrets.

---

## References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest.ini](../../pytest.ini)
- [.coveragerc](../../.coveragerc)
- [conftest.py](../../conftest.py)
