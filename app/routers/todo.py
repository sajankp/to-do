from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Request

from app.models.todo import Todo, TodoBase

router = APIRouter()


@router.get("/", response_model=List[Todo])
def get_todo_list(request: Request):
    books = list(request.app.todo.find().limit(100))
    return books


@router.post("/", response_model=TodoBase)
def create_todo(request: Request, todo: TodoBase):
    try:
        current_time = datetime.utcnow()

        new_todo = Todo(
            title=todo.title,
            description=todo.description,
            due_date=todo.due_date,
            priority=todo.priority,
            created_at=current_time,
            updated_at=current_time,
        )
        result = request.app.todo.insert_one(new_todo.dict())
        if result.acknowledged:
            return new_todo
        else:
            # Handle the case where insertion failed
            raise HTTPException(status_code=500, detail="Failed to create todo")
    except Exception as e:
        # Handle any exceptions or validation errors here
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{todo_id}")
def update_todo(todo_id: str):
    # Your code to update a todo
    pass


@router.delete("/{todo_id}")
def delete_todo(todo_id: str):
    # Your code to delete a todo
    pass
