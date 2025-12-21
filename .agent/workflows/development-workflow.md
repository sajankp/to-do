---
description: Mandatory workflow for new features and architectural changes
---

# Development Workflow for New Features

This workflow MUST be followed for any new feature or architectural change.

## ⚠️ Critical Rule: No Code Before Documentation

**DO NOT** jump straight to implementation. Follow this sequence:

```
1. Update spec.md (don't commit)
   ↓
2. CHECKPOINT: User reviews spec.md → approves → commit spec.md
   ↓
3. Create ADR (don't commit)
   ↓
4. CHECKPOINT: User reviews ADR → approves → commit ADR
   ↓
5. Implement code
```

> [!CAUTION]
> **INCREMENTAL REVIEW PROCESS**
> - After spec.md: STOP and request review
> - After ADR: STOP and request review
> - Only proceed to next step after explicit approval
> - Commits happen ONLY after each checkpoint approval

## Step-by-Step Process

### Step 1: Update spec.md

When a new feature or architectural change is proposed:

1. Open `docs/spec.md`
2. Add discussion to the appropriate section:
   - **New architectural concern**: Add to "Known Architectural Pitfalls"
   - **New decision**: Add to "Architectural Decisions Summary"
   - **New model field**: Update "Data Models" section
   - **New API endpoint**: Update "API Contract" section
3. Include:
   - **Context**: Why is this needed?
   - **Options Considered**: What alternatives exist?
   - **Trade-offs**: What are the pros/cons?
   - **Decision**: What approach are we taking?
4. **STOP HERE** - Do not commit, do not create ADR yet

### Step 2: CHECKPOINT - Review spec.md

Use `notify_user` to request review of spec.md ONLY:

```
PathsToReview: ["/absolute/path/to/docs/spec.md"]
BlockedOnUser: true
Message: "I've updated spec.md with the proposed changes. Please review.
         If approved, I'll commit and proceed to create the ADR."
```

**Wait for user response:**
- ✅ User approves → Proceed to Step 3
- ❌ User requests changes → Update spec.md, return to Step 2
- ⏸️ User defers → Stop, don't proceed

### Step 3: Commit spec.md (ONLY AFTER APPROVAL)

Once user approves spec.md:
1. Stage: `git add docs/spec.md`
2. Commit: `docs: add [feature description] to specification`
3. **STOP HERE** - Do not create ADR yet, wait for explicit instruction

### Step 4: Create ADR

Once user instructs to proceed:

Create Architecture Decision Record in `docs/adr/`:

```bash
# Naming convention: NNN-descriptive-title.md
# Example: 009-add-todo-completion-status.md
```

ADR should include:
- **Status**: Proposed | Accepted | Rejected
- **Context**: Background and problem statement
- **Decision**: What we decided to do
- **Consequences**: Impact of this decision
- **Alternatives Considered**: Other options we rejected

**STOP HERE** - Do not commit ADR yet

### Step 5: CHECKPOINT - Review ADR

Use `notify_user` to request review of ADR ONLY:

```
PathsToReview: ["/absolute/path/to/docs/adr/XXX-....md"]
BlockedOnUser: true
Message: "I've created ADR XXX. Please review.
         If approved, I'll commit and proceed to implementation."
```

**Wait for user response:**
- ✅ User approves → Proceed to Step 6
- ❌ User requests changes → Update ADR, return to Step 5
- ⏸️ User defers → Stop, don't proceed

### Step 6: Commit ADR (ONLY AFTER APPROVAL)

Once user approves ADR:
1. Stage: `git add docs/adr/XXX-....md`
2. Commit: `docs: create ADR-XXX for [feature]`
3. **STOP HERE** - Do not start implementation yet

### Step 7: Implement Code (ONLY AFTER EXPLICIT INSTRUCTION)

Only after user explicitly instructs to proceed with implementation:
1. Create feature branch (if not already on one)
2. Implement backend changes
3. Write tests
4. Implement frontend changes
5. Create PR referencing the ADR

## Examples of Changes Requiring This Workflow

✅ **Requires workflow**:
- Adding new model fields (e.g., `completed` field)
- New API endpoints
- Authentication/security changes
- Database schema changes
- New architectural patterns (repository layer, service layer)
- Breaking changes
- Major refactors

❌ **Does NOT require workflow** (minor changes):
- Bug fixes
- UI styling tweaks
- Code formatting
- Documentation fixes
- Test additions

## Enforcement

If you see me jumping to implementation without following this workflow:

1. **Stop me immediately**
2. **Remind me**: "Follow the spec.md workflow: discuss → spec.md → ADR → approve → implement"
3. **I will backtrack** and do it properly

## Why This Matters

- **Prevents technical debt**: Decisions are documented with context
- **Future maintainers**: Understand the "why" behind choices
- **Accountability**: Clear record of architectural decisions
- **Thoughtful design**: Forces consideration of alternatives
- **Team alignment**: Everyone understands the architecture

---

**Current Status**: ✅ Workflow established 2025-12-21
