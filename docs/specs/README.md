# Feature Specifications

This folder contains detailed specifications for features written **before implementation**, following [Spec-Driven Development (SDD)](https://github.blog/changelog/2025-06-03-spec-kit-public-beta/) practices.

## Why Spec-Driven Development?

- **Clarity**: Define exactly what to build before writing code
- **Review**: Get approval on approach before investing time
- **AI-Friendly**: Specs serve as clear instructions for AI agents
- **Documentation**: Specs become living documentation

## Workflow

```
1. Create spec in this folder
2. Get approval
3. Implement following the spec
4. Spec becomes documentation
```

See [development workflow](../../.agent/workflows/development-workflow.md) for the full process.

---

## Index of Specs

| ID | Title | Status | ADR |
|----|-------|--------|-----|
| 001 | [Todo Completion Status](001-todo-completion.md) | ✅ Implemented | [ADR-009](../adr/009-add-todo-completion-status.md) |
| 002 | [Gemini API Backend Proxy](002-gemini-api-proxy.md) | 📋 Planned | [ADR-008](../adr/008-gemini-api-backend-proxy.md) |
| 003 | Security Headers Middleware | 📋 Planned | - |

---

## Spec Template

When creating a new spec, use this template:

```markdown
# Spec: [Feature Name]

## Status
Draft | In Review | Approved | Implemented | Rejected

## Problem Statement
What problem does this solve? Why is this needed?

## Proposed Solution
High-level approach to solving the problem.

## API Changes

### New Endpoints
- `POST /api/...` - Description

### Modified Endpoints
- `GET /api/...` - What changes

### Request/Response Format
\`\`\`json
{
  "field": "value"
}
\`\`\`

## Data Model Changes

### New Fields
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `completed` | `bool` | `false` | Whether todo is done |

### New Collections
(If applicable)

## Implementation Plan

1. Backend: Add field to model
2. Backend: Update API endpoints
3. Backend: Write tests
4. Frontend: Update UI components
5. Frontend: Add toggle functionality

## Test Strategy

### Unit Tests
- Test field validation
- Test default values

### Integration Tests
- Test full workflow

### Manual Verification
- Steps to manually verify

## Open Questions
- [ ] Question that needs clarification
- [x] Resolved question - answer here

## Related
- **ADR**: Pending | Not required | [ADR-NNN](../adr/NNN-....md)
- **Issue**: [#XX](https://github.com/sajankp/to-do/issues/XX) (if applicable)
- **Depends on**: [Spec-NNN](NNN-....md) (if applicable)
```

---

## Status Definitions

| Status | Meaning |
|--------|---------|
| **Draft** | Initial creation, not ready for review |
| **In Review** | Awaiting approval |
| **Approved** | Ready for implementation |
| **Implemented** | Feature is complete |
| **Rejected** | Decided not to implement |
| **Superseded** | Replaced by another spec |
