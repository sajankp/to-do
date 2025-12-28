# ADR-009: Add Todo Completion Status Field

## Status
Proposed

## Context
The current Todo application supports basic CRUD (Create, Read, Update, Delete) operations but lacks a fundamental feature: the ability to mark a task as completed.

Currently, users have two suboptimal choices when they finish a task:
1. Leave it in the active list alongside incomplete tasks, causing clutter.
2. Delete the task immediately to remove it from view, which loses the historical record of accomplishment and prevents any future productivity tracking.

To provide a professional todo management experience, we need a way to track the lifecycle of a task beyond just creation and deletion.

## Decision
We will add a binary `completed` field to the Todo model and update the system across all layers.

### Technical Details:
1. **Data Layer**: Add a `completed` boolean field to the MongoDB document, defaulting to `false`.
2. **API Layer**:
   - Update Pydantic models (`TodoInput`, `TodoUpdate`, `TodoInDB`, `TodoResponse`) to include the field.
   - Add filtering support to `GET /todo/` via a `completed` query parameter.
   - Ensure `PATCH /todo/{id}` correctly handles updating this field.
3. **Frontend Layer**:
   - Update TypeScript interfaces.
   - Implement UI controls (checkboxes) in `TodoList.tsx`.
   - Add visual feedback (strikethrough and reduced opacity) for completed items.
   - Implement filtering tabs (All / Active / Completed).

### Why a Boolean instead of an Enum?
While a status enum (Todo, InProgress, Done) would offer more states, the current requirement is strictly binary. A boolean is simpler to implement, more efficient for indexing, and adheres to the YAGNI (You Aren't Gonna Need It) principle. We can migrate to an enum in the future if complex workflows are required.

## Consequences

### Positive:
- **Improved UX**: Users can see their progress and maintain a history of completed work.
- **Better Filtering**: The UI can now hide noise while keeping data accessible.
- **Backward Compatibility**: Existing records in MongoDB will naturally default to `false` when loaded into the new Pydantic models.

### Negative / Trade-offs:
- **Model Complexity**: Slight increase in the number of fields to manage.
- **Database Indexing**: To maintain performance at scale, we should create a compound index on `(user_id, completed)`.

## Alternatives Considered
- **Separate Collection**: Moving completed items to a `history` collection. *Rejected* because it complicates retrieval and search functionality.
- **Soft Delete**: Using a `deleted_at` field to hide tasks. *Rejected* because "Completed" is a functional state, whereas "Deleted" usually implies a mistake or removal from the system.
