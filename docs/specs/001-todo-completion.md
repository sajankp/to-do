# Spec: Todo Completion Status

## Status
📝 Proposed

## Problem Statement

Current todo implementation supports Create, Read, Update, Delete operations but lacks a way to mark tasks as complete. Users must delete completed tasks, losing history and preventing productivity tracking.

**Issues:**
- No completion status tracking
- Users cannot differentiate between active and completed tasks
- Deleting completed tasks loses historical data
- Cannot track productivity metrics (completion rate, time to complete)

## Proposed Solution

Add a boolean `completed` field to the Todo model with filtering support.

```
Todo {
  ...existing fields...
  completed: bool = false
}
```

## API Changes

### Modified Endpoints

#### `GET /todo/`
Add optional query parameter for filtering:
- `?completed=true` - Return only completed todos
- `?completed=false` - Return only active todos
- (no param) - Return all todos

#### `PATCH /todo/{id}`
Allow updating the `completed` field.

### Request/Response Format

```json
{
  "id": "...",
  "title": "...",
  "description": "...",
  "priority": "medium",
  "due_date": "2025-01-01T00:00:00Z",
  "completed": false
}
```

## Data Model Changes

### Backend Models

| Model | Field | Type | Default |
|-------|-------|------|---------|
| `TodoInput` | `completed` | `bool` | `False` |
| `TodoUpdate` | `completed` | `Optional[bool]` | `None` |
| `TodoInDB` | `completed` | `bool` | `False` |
| `TodoResponse` | `completed` | `bool` | `False` |

### Database Index
```python
todos.create_index([("user_id", 1), ("completed", 1)])
```

## Implementation Plan

### Backend
1. [ ] Add `completed: bool = False` to all todo models
2. [ ] Update GET `/todo/` to support `?completed=` query param
3. [ ] Ensure PATCH `/todo/{id}` can update `completed`
4. [ ] Add database index for efficient filtering
5. [ ] Write unit tests for new field
6. [ ] Write integration tests for filtering

### Frontend
1. [ ] Add `completed: boolean` to Todo TypeScript interface
2. [ ] Add checkbox to task cards
3. [ ] Visual styling: strikethrough + reduced opacity for completed
4. [ ] Filter UI: Tabs for "All" / "Active" / "Completed"
5. [ ] Default view: Active only

## Test Strategy

### Unit Tests
- [ ] TodoInput accepts `completed` field
- [ ] Default value is `False`
- [ ] Validation rejects non-boolean values

### Integration Tests
- [ ] Create todo → completed defaults to false
- [ ] Update todo with completed=true → persists
- [ ] Filter by completed=true returns only completed
- [ ] Filter by completed=false returns only active

### Manual Verification
- [ ] Create todo, verify checkbox unchecked
- [ ] Click checkbox, verify strikethrough appears
- [ ] Refresh page, verify state persists

## UX Decisions

| Decision | Choice |
|----------|--------|
| Completed styling | Strikethrough + 60% opacity |
| Checkbox position | Left side of task card |
| Sort order | Completed tasks at bottom |
| Default filter | Active only |

## Trade-offs Accepted

- Limited to binary state (can't track "in progress")
- Completed tasks remain in main collection (slight query overhead)
- No automatic archival of old completed tasks

## Migration Strategy

- No database migration required (MongoDB schemaless)
- Existing documents without `completed` field default to `False` via Pydantic
- New todos explicitly set `completed=False` on creation

## Related

- [ADR-009: Add Todo Completion Status](../adr/009-add-todo-completion-status.md)
- Decision context from architecture review 2025-12-21
