# Contributing to FastTodo

Thank you for your interest in contributing to FastTodo! This document outlines our development process and guidelines.

## Development Workflow

We follow **Spec-Driven Development (SDD)** for new features and architectural changes:

```
1. Create Feature Spec → Get approval
2. Create ADR (if architectural decision) → Get approval
3. **New Branch** → Implement → Test → PR
```

For detailed workflow instructions, see:
- [Development Workflow](.agent/workflows/development-workflow.md)
- [Feature Specs](docs/specs/)

## Quick Start

### Prerequisites
- Python 3.13
- MongoDB (local or Atlas)
- Git

### Setup

```bash
# Clone and setup
git clone https://github.com/sajankp/to-do.git
cd to-do
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pre-commit install

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run tests
pytest app/tests/
```

## Making Changes

### For Bug Fixes / Small Changes

1. Create a branch: `git checkout -b fix/description`
2. Make changes
3. Run tests: `pytest app/tests/`
4. Commit using [conventional commits](#commit-format)
5. Push and create PR

### For New Features / Architectural Changes

1. **Create a feature spec** in `docs/specs/NNN-feature.md`
2. Get approval on the spec
3. Create ADR if architectural decision was made
4. Implement following the spec
5. Open PR referencing the spec

## Commit Format

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <description>

[optional body]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding tests
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

**Examples:**
```bash
git commit -m "feat: add todo completion status field"
git commit -m "fix: resolve MongoDB connection timeout"
git commit -m "docs: update API documentation"
```

## Code Quality

Pre-commit hooks run automatically on commit:
- Ruff linting and formatting
- Conventional commit message validation
- Trailing whitespace removal

Run manually:
```bash
pre-commit run --all-files
```

## Testing

```bash
# Run all tests
pytest app/tests/

# With coverage
pytest --cov=app --cov-report=term-missing

# Specific test file
pytest app/tests/routers/test_auth.py -v
```

## Documentation

- **[Documentation Index](docs/README.md)** - **Start here**
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture
- **[Feature Specs](docs/specs/)** - Feature specifications (SDD)
- **[ADRs](docs/adr/)** - Architectural decisions
- **[ROADMAP.md](docs/ROADMAP.md)** - Priorities
- **[AGENTS.md](AGENTS.md)** - AI Agent context

## Questions?

- Open a [GitHub Issue](https://github.com/sajankp/to-do/issues)
- Check existing [documentation](docs/)

---

*Thank you for contributing!*
