from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Request
from models.todo import Todo, TodoBase

router = APIRouter()


@router.get("/", response_model=List[Todo])
def get_todo_list(request: Request):
    books = list(request.app.todo.find().limit(100))
    return books
    


@router.post("/", response_model=TodoBase)
def create_todo(todo: TodoBase):
    try:
        # Get the current timestamp
        current_time = datetime.utcnow()

        # Create a new todo using the provided data
        new_todo = Todo(
            title=todo.title,
            description=todo.description,
            due_date=todo.due_date,
            priority=todo.priority,
            created_at=current_time, 
            updated_at=current_time,  
        )

        
        return new_todo
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
