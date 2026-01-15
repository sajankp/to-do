---
description: Spec-driven development workflow for new features and architectural changes
---

# Spec-Driven Development Workflow

This workflow MUST be followed for any new feature or architectural change.

## ⚠️ Core Principle: Specification Before Implementation

**DO NOT** jump straight to coding. Follow the Spec-Driven Development (SDD) process:

```
1. Create Feature Spec (docs/specs/NNN-feature.md)
   ↓
2. CHECKPOINT: User reviews spec → Approve
   ↓
3. Create ADR (if architectural decision was made)
   ↓
4. (If ADR) CHECKPOINT: User reviews ADR → Approve
   ↓
5. Create feature branch and commit approvals
   ↓
6. Implement code (following the spec exactly)
   ↓
7. Update ARCHITECTURE.md (only if system architecture changed)
   ↓
8. Create PR with all changes
```

> [!CAUTION]
> **INCREMENTAL REVIEW PROCESS**
> - After creating spec: STOP and request review
> - After creating ADR (if needed): STOP and request review
> - Only proceed to next step after explicit approval

---

## 🧭 Decision Flowchart: Do I Need This Workflow?

Before starting, ask yourself:

```
Is this a new user-facing feature or API change?
├── YES → Full SDD workflow (spec required)
└── NO → Is it a breaking change to existing behavior?
         ├── YES → Full SDD workflow
         └── NO → Is it CI/infra/dependency maintenance?
                  ├── YES → Direct fix (no spec needed)
                  └── NO → Bug fix or minor refactor?
                           ├── YES → Direct fix (no spec needed)
                           └── UNSURE → Ask the user
```

---

## Step-by-Step Process

### Step 1: Create Feature Spec

When a new feature or change is proposed:

1. Create a new file in `docs/specs/` with naming: `NNN-descriptive-title.md`
2. Use the template in `docs/specs/README.md`
3. Include:
   - **Problem Statement**: Why is this needed?
   - **Proposed Solution**: How will we solve it?
   - **API Changes**: New/modified endpoints, request/response format
   - **Data Model Changes**: Schema changes, new fields
   - **Implementation Plan**: Step-by-step approach
   - **Test Strategy**: How to verify correctness
   - **Open Questions**: Things to clarify

4. **STOP HERE** - Do not commit, do not create ADR yet

### Step 2: CHECKPOINT - Review Spec

Use `notify_user` to request review of the spec ONLY:

```
PathsToReview: ["/absolute/path/to/docs/specs/NNN-feature.md"]
BlockedOnUser: true
Message: "I've created a feature spec. Please review.
         If approved, I'll commit and proceed."
```

**Wait for user response:**
- ✅ User approves → Proceed to Step 3
- ❌ User requests changes → Update spec, return to Step 2
- ⏸️ User defers → Stop, don't proceed

### Step 3: Create ADR (If Needed)

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
2. Include:
   - **Context**: Background and problem
   - **Options Considered**: What alternatives existed
   - **Decision**: What we chose and why
   - **Consequences**: Trade-offs accepted

3. **STOP HERE** - Request review before committing

### Step 4: CHECKPOINT - Review ADR (If Applicable)

Use `notify_user` to request review of ADR:

```
PathsToReview: ["/absolute/path/to/docs/adr/NNN-....md"]
BlockedOnUser: true
Message: "I've created ADR-NNN. Please review.
         If approved, I'll create feature branch and proceed to implementation."
```

### Step 5: Create Feature Branch and Commit Approvals

Once user approves spec (and ADR if applicable):

1. **Create feature branch:**
   ```bash
   git checkout -b feat/descriptive-name
   ```

2. **Update spec/ADR status to approved:**
   - Change spec status from "Planned" to "Approved"
   - Change ADR status from "Proposed" to "Accepted" (if applicable)

3. **Stage and commit approval updates:**
   ```bash
   git add docs/specs/NNN-*.md
   git add docs/adr/NNN-*.md  # if ADR exists
   git commit -m "docs: approve spec-NNN and ADR-NNN for [feature]"
   ```

4. **Verify commit:**
   ```bash
   git log --oneline -1
   git status  # Should show clean working tree
   ```

### Step 6: Implement Code

Only after spec (and ADR if applicable) are approved:
1. **CRITICAL:** Create a dedicated feature branch (e.g., `feat/my-feature`).
   - Command: `git checkout -b feat/my-feature`
   - **Agent/User Check:** Confirm with the user: "I am creating/switching to branch `[branch_name]` to implement this. Is that correct?"
2. Implement backend changes **following the spec exactly**
3. Write tests as defined in spec
4. Implement frontend changes (if applicable)
5. Run tests, ensure passing
6. Commit with conventional commit format

### Step 7: Update ARCHITECTURE.md (After Implementation)

Update `docs/ARCHITECTURE.md` **only if** the system architecture actually changed:
- New component added
- New architectural pattern introduced
- Security model changed
- Data flow changed

**When to update:**
- ✅ **AFTER implementation** - in the same PR/commit as the code
- ✅ When the change is system-level (affects architecture diagram)
- ❌ NOT for implementation details (which library, which algorithm)

**Examples:**
- ✅ Add new middleware → Update ARCHITECTURE.md (new component in diagram)
- ✅ Change auth flow → Update ARCHITECTURE.md (security model changed)
- ❌ Migrate bcrypt → Argon2id → Don't update (same auth model, different implementation)
- ❌ Upgrade pytest version → Don't update (dependency, not architecture)

**What to update:**
- System diagrams if component added
- Security architecture table if security model changed
- Component specifications if responsibilities changed

**Do NOT** add detailed feature specs to ARCHITECTURE.md. That content stays in `docs/specs/`.

### Step 8: Create PR and Run Tests

After implementation is complete:

1. Push the feature branch: `git push -u origin feat/my-feature`
2. Create PR: `gh pr create --title "feat: [description]" --body "Closes #issue"`
3. Run full test suite locally and confirm all tests pass
4. **STOP** - Follow `/pr-review` workflow to process the PR

> [!TIP]
> After implementation, use `/pr-review` to process the PR through AI review and merge.

---

## Document Purposes

| Document | Purpose | Contains |
|----------|---------|----------|
| `docs/specs/*.md` | Feature blueprint | Problem, solution, API, implementation plan |
| `docs/adr/*.md` | Decision record | Options, trade-offs, why we chose this |
| `docs/ARCHITECTURE.md` | System overview | Current state, not decision history |
| `docs/ROADMAP.md` | Planning | Phases, priorities, technical debt |

---

## Examples

### ✅ Requires This Workflow
- Adding new model fields (e.g., `completed` field)
- New API endpoints
- Authentication/security changes
- Database schema changes
- New architectural patterns
- Breaking changes
- Major refactors

### ❌ Does NOT Require Workflow (Minor Changes)
- Bug fixes
- UI styling tweaks
- Code formatting
- Documentation fixes
- Adding tests to existing code
- **CI/Infrastructure fixes** (workflow files, Dependabot, pre-commit configs)
- **Dependency updates** (unless they require code changes beyond version bumps)
- **Configuration changes** for test/CI environments
- **Routine security patches**

### 🤔 When Unsure

If the change:
1. Has **no user-facing impact** AND
2. Doesn't **change API contracts** AND
3. Doesn't **alter data models**

→ It's likely a minor change. When in doubt, ask the user.

---

## Why This Matters

- **Spec-Driven Development**: Industry-standard approach used by AWS Kiro, GitHub Spec Kit
- **Clear blueprints**: Specs define exactly what to build
- **Decision transparency**: ADRs capture the "why"
- **Clean architecture docs**: ARCHITECTURE.md stays lean
- **AI-friendly**: Specs serve as clear instructions for AI agents

---

## Enforcement

If you see me jumping to implementation without following this workflow:

1. **Stop me immediately**
2. **Remind me**: "Follow the SDD workflow: spec → approve → ADR (if needed) → implement"
3. **I will backtrack** and do it properly

---

*Workflow established: 2025-12-21*
*Updated to SDD: 2025-12-28*
*Added decision criteria: 2025-12-30*
