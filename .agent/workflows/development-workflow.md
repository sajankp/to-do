---
description: Spec-driven development workflow with mandatory TDD for new features and architectural changes
---

# Spec-Driven Development Workflow with TDD

This workflow MUST be followed for any new feature or architectural change.

## ⚠️ Core Principle: Specification Before Implementation, Tests Before Code

**DO NOT** jump straight to coding. Follow the Spec-Driven Development (SDD) process with mandatory TDD:

```
Phase 0: Discovery (optional)     → Research if needed
    ↓
Phase 1: Specification            → Create spec, get approval
    ↓
Phase 2: Test-First (TDD Red)     → Write failing tests
    ↓
Phase 3: Implementation (TDD Green) → Make tests pass
    ↓
Phase 4: Refactor                 → Clean up, keep tests green
    ↓
Phase 5: Verification             → Validate against spec
    ↓
Phase 6: Pull Request             → Create PR, follow /pr-review
```

> [!CAUTION]
> **INCREMENTAL REVIEW PROCESS**
> - After creating spec: STOP and request review
> - After creating ADR (if needed): STOP and request review
> - After writing tests: STOP and request review (test case checkpoint)
> - After implementation: Verify spec match before PR
> - Before EVERY commit: Request explicit user approval

---

## 🚨 Scope Check: Does This Need the Full Workflow?

Before starting any work, evaluate using this **hybrid criteria**:

```
┌────────────────────────────────────────────────────────────┐
│  TRIGGER FULL SDD WORKFLOW IF ANY ARE TRUE:                │
├────────────────────────────────────────────────────────────┤
│  □ Time estimate > 2 hours                                 │
│  □ Touching > 3 files                                      │
│  □ Risk surface: auth, DB schema, or API contracts         │
│  □ Second touch on same area within a week                 │
│  □ Can't explain the change in one sentence                │
├────────────────────────────────────────────────────────────┤
│  If ANY box is checked → Use full workflow                 │
│  If NONE → Proceed with minor fix (but stay vigilant)      │
└────────────────────────────────────────────────────────────┘
```

> [!TIP]
> **The gut check rule:** If you're asking "Should this have a spec?" → It probably should.

### ✅ Requires This Workflow
- Adding new model fields (e.g., `completed` field)
- New API endpoints
- Authentication/security changes
- Database schema changes
- New architectural patterns
- Breaking changes
- Major refactors

### ❌ Does NOT Require Workflow (Minor Changes)
- Bug fixes (single file, clear cause)
- UI styling tweaks
- Code formatting
- Documentation fixes
- Adding tests to existing code
- **CI/Infrastructure fixes** (workflow files, Dependabot, pre-commit configs)
- **Dependency updates** (unless they require code changes beyond version bumps)
- **Configuration changes** for test/CI environments
- **Routine security patches**

### 🚦 Scope Creep Alert

If a "minor fix" starts hitting the triggers above:
1. **STOP** immediately
2. **Document** what you've done so far
3. **Notify user**: "This grew beyond a minor fix. Should I create a spec?"

---

## Phase 0: Discovery (Optional)

Use this phase when you need to **research before specifying**.

### When to Use
- Exploring unfamiliar patterns (e.g., FastAPI async, OpenTelemetry)
- Comparing implementation options
- Understanding third-party API behavior
- Learning new libraries

### What to Do
1. **Time-box** exploration (suggest: 30-60 minutes max)
2. **Document findings** (in chat, not committed files)
3. **Summarize options** with trade-offs
4. **Ask user** to confirm direction before writing spec

### Output
- Understanding, not code
- Clear recommendation for spec

---

## Phase 1: Specification

### Step 1.1: Create Feature Spec

When a new feature or change is proposed:

1. Create a new file in `docs/specs/` with naming: `NNN-descriptive-title.md`
2. Use the template in `docs/specs/README.md`
3. Include:
   - **Problem Statement**: Why is this needed?
   - **Proposed Solution**: How will we solve it?
   - **API Changes**: New/modified endpoints, request/response format
   - **Data Model Changes**: Schema changes, new fields
   - **Implementation Plan**: Step-by-step approach
   - **Test Strategy**: How to verify correctness (TDD will use this)
   - **Open Questions**: Things to clarify

4. **STOP HERE** - Do not commit, do not create ADR yet

### Step 1.2: CHECKPOINT - Review Spec

Use `notify_user` to request review of the spec ONLY:

```
PathsToReview: ["/absolute/path/to/docs/specs/NNN-feature.md"]
BlockedOnUser: true
Message: "I've created a feature spec. Please review.
         If approved, I'll proceed to ADR (if needed) or TDD."
```

**Wait for user response:**
- ✅ User approves → Proceed to Step 1.3 or Phase 2
- ❌ User requests changes → Update spec, return to review
- ⏸️ User defers → Stop, don't proceed

### Step 1.3: Create ADR (If Needed)

Create an ADR **only if** you made a non-obvious choice between alternatives.

**When ADR is needed:**
- Chose between multiple architectural options
- Made a trade-off decision
- Established a new pattern

**When ADR is NOT needed:**
- Straightforward feature implementation
- Following existing patterns
- No alternatives were considered

If ADR is needed:
1. Create in `docs/adr/` with naming: `NNN-descriptive-title.md`
2. Include Context, Options Considered, Decision, Consequences
3. **STOP HERE** - Request review before proceeding

### Step 1.4: CHECKPOINT - Review ADR (If Applicable)

```
PathsToReview: ["/absolute/path/to/docs/adr/NNN-....md"]
BlockedOnUser: true
Message: "I've created ADR-NNN. Please review.
         If approved, I'll create feature branch and write tests."
```

---

## Phase 2: Test-First (TDD Red Phase)

> [!IMPORTANT]
> **TDD IS MANDATORY.** Tests must be written BEFORE implementation code.

### Step 2.1: Create Feature Branch

```bash
git checkout -b feat/descriptive-name
```

### Step 2.2: Update Spec Status

Change spec status from "Planned" to "Approved" (and ADR if applicable).

### Step 2.3: Write Failing Tests

Based on the spec's **Test Strategy** section:

1. **Create test file(s)** in the appropriate test directory
2. **Write test cases** that cover:
   - Happy path scenarios
   - Edge cases
   - Error handling
   - Security constraints (if applicable)
3. **Tests MUST fail** initially:
   - This proves they're testing something real
   - If tests pass without implementation, they're useless

```bash
# Run tests - they SHOULD fail (use appropriate runner)
# Backend: pytest app/tests/path/to/test_file.py -v
# Frontend: npm run test -- path/to/test_file.tsx

# Expected output: FAILED (red phase)
```

> [!TIP]
> Use the `/tdd-fastapi` skill for FastAPI-specific testing patterns, or adapt for frontend (Vitest).

### Step 2.4: CHECKPOINT - Review Test Cases

```
PathsToReview: ["/absolute/path/to/app/tests/..."]
BlockedOnUser: true
Message: "I've written failing tests per the spec's Test Strategy.
         Tests fail as expected (Red phase). Please review test coverage.
         After approval, I'll implement to make them pass."
```

### Step 2.5: CHECKPOINT - Pre-Commit Approval

```bash
git add app/tests/...
```

Request approval:
```
Message: "Ready to commit test scaffolding with message:
         'test: add failing tests for [feature]'
         Proceed?"
```

**Only commit after explicit approval.**

Verify commit succeeded:
```bash
git log --oneline -1
git status  # Should be clean
```

---

## Phase 3: Implementation (TDD Green Phase)

### Step 3.1: Implement Code

1. **Make tests pass** - Focus on the simplest solution
2. **Follow spec exactly** - Don't add unrequested features
3. **Run tests frequently** - After each significant change

```bash
# Run tests - work until they pass (use appropriate runner)
# Backend: pytest app/tests/path/to/test_file.py -v
# Frontend: npm run test -- path/to/test_file.tsx

# Expected output: PASSED (green phase)
```

### Step 3.2: Handle Spec Gaps (Iteration Protocol)

During implementation, if you discover issues:

| Discovery | Action |
|-----------|--------|
| **Spec gap** (missing requirement) | STOP → Explain what's missing and why → User decides: update spec or defer |
| **Spec ambiguity** (unclear) | STOP → Explain options → User clarifies → Update spec → Continue |
| **Spec wrong** (can't implement as written) | STOP → Explain issue and alternative → User revises spec → Continue |
| **Unexpected complexity** | Re-check scope triggers → If hit, escalate to full workflow |

> [!CAUTION]
> **Always discuss spec issues with user.** Don't silently deviate from the spec or make assumptions.

### Step 3.3: CHECKPOINT - Pre-Commit Approval

```bash
git add app/...  # Implementation files
```

Request approval:
```
Message: "Ready to commit implementation with message:
         'feat: implement [feature]'
         All tests passing. Proceed?"
```

Verify:
```bash
git log --oneline -1
git status
```

---

## Phase 4: Refactor (TDD Refactor Phase)

### Step 4.1: Clean Up Code

With tests green, improve code quality:
- Remove duplication (DRY)
- Improve naming and readability
- Optimize performance (if needed)
- Add type hints (if missing)

### Step 4.2: Keep Tests Green

```bash
# After each refactor, verify tests still pass (use appropriate runner)
# Backend: pytest app/tests/path/to/test_file.py -v
# Frontend: npm run test -- path/to/test_file.tsx
```

### Step 4.3: CHECKPOINT - Pre-Commit Approval (If Changes Made)

If refactoring resulted in meaningful changes:

```bash
git add -A
```

Request approval:
```
Message: "Ready to commit refactoring with message:
         'refactor: clean up [feature] implementation'
         All tests still passing. Proceed?"
```

---

## Phase 5: Verification

### Step 5.1: Run Full Test Suite

```bash
# All tests, with coverage (use appropriate runner)
# Backend: pytest --cov=app --cov-report=term-missing app/tests/
# Frontend: npm run test:coverage
```

All tests must pass. Coverage should meet project threshold.

### Step 5.2: Integration/Manual Testing

Per the spec's verification plan:
- Test with actual MongoDB (if integration tests defined)
- Manual testing for UI-affecting changes
- API testing via Swagger UI

### Step 5.3: CHECKPOINT - Verify Spec Match

Review the spec and confirm:

- [ ] All requirements implemented
- [ ] All test cases from Test Strategy covered
- [ ] No unrequested features added
- [ ] Edge cases handled as specified

If spec match fails: Go back to Phase 3.

### Step 5.4: Update Spec Status

Change spec status from "Approved" to "Implemented".

---

## Phase 6: Pull Request

### Step 6.1: Push Feature Branch

```bash
git push -u origin feat/descriptive-name
```

### Step 6.2: Create PR

Create a pull request for the feature branch. Ensure the title follows the conventional commits format (e.g., "feat: [description]") and the body references any issues it closes (e.g., "Closes #123").

### Step 6.3: Fill Post-Deployment Checklist

If changes require deployment tasks (new env vars, migrations, etc.), complete the PR template checklist.

### Step 6.4: Follow /pr-review Workflow

```
→ See /.agent/workflows/pr-review.md
```

### Step 6.5: Post-Merge Cleanup

After PR is merged:
- Update ROADMAP.md if applicable
- Close related issues
- Update ARCHITECTURE.md if system architecture changed

---

## Commit Guidance

### Commit Frequency

**One commit per phase** (preferred):
- `docs: add spec-NNN for [feature]` (Phase 1)
- `test: add failing tests for [feature]` (Phase 2)
- `feat: implement [feature]` (Phase 3)
- `refactor: clean up [feature]` (Phase 4, if applicable)

**Multiple commits within a phase** (when needed):
- If touching > 5 files in a phase, consider logical splits
- Group by component (e.g., models, routers, tests)

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New feature
- `fix:` Bug fix
- `test:` Adding/updating tests
- `refactor:` Code improvement (no behavior change)
- `docs:` Documentation changes
- `chore:` Maintenance (deps, CI, etc.)

### Pre-Commit Verification

After EVERY commit:
```bash
git log --oneline -1  # Verify commit in history
git status            # Check for uncommitted changes (pre-commit failure)
```

If `git status` shows changes after commit → pre-commit hook failed → fix and retry.

---

## Document Purposes

| Document | Purpose | Contains |
|----------|---------|----------|
| `docs/specs/*.md` | Feature blueprint | Problem, solution, API, implementation plan, test strategy |
| `docs/adr/*.md` | Decision record | Options, trade-offs, why we chose this |
| `docs/ARCHITECTURE.md` | System overview | Current state, not decision history |
| `docs/ROADMAP.md` | Planning | Phases, priorities, technical debt |

---

## Why This Matters

- **Spec-Driven Development**: Industry-standard approach (AWS Kiro, GitHub Spec Kit)
- **Mandatory TDD**: Catches bugs early, forces good design
- **Clear checkpoints**: Ensures user alignment at every stage
- **Iteration protocol**: Handles real-world complexity gracefully
- **AI-friendly**: Specs + tests serve as clear instructions for agents

---

## Enforcement

If you see me:
- Jumping to implementation without spec → STOP, remind me of SDD
- Writing code before tests → STOP, remind me of TDD
- Committing without approval → This violates global rules
- Deviating from spec silently → STOP, require explicit discussion

---

*Workflow established: 2025-12-21*
*Updated to SDD: 2025-12-28*
*Added decision criteria: 2025-12-30*
*Added TDD + enhanced checkpoints: 2026-01-18*
