from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.models.todo import PyObjectId, Todo, TodoBase, TodoCreate, TodoUpdate
from app.models.user import User
from app.routers.auth import get_current_active_user
from app.utils.constants import (
    FAILED_DELETE_TODO,
    NO_CHANGES,
    TODO_DELETED_SUCCESSFULLY,
    TODO_NOT_FOUND,
    TODO_UPDATED_SUCCESSFULLY,
)

router = APIRouter()


@router.get("/", response_model=List[TodoBase])
def get_todo_list(request: Request, user: User = Depends(get_current_active_user)):
    todos = list(request.app.todo.find({"user_id": user.id}).limit(100))
    return todos


@router.get("/{todo_id}", response_model=TodoBase)
def get_todo(todo_id: PyObjectId, request: Request):
    todo = request.app.todo.find_one({"_id": todo_id})
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=TODO_NOT_FOUND
        )
    return todo


@router.post("/", response_model=TodoBase)
def create_todo(request: Request, todo: TodoCreate):
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
        new_todo.id = result.inserted_id
        return new_todo
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=FAILED_DELETE_TODO,
        )


@router.put("/{todo_id}")
def update_todo(todo: TodoUpdate, request: Request):
    existing_todo = request.app.todo.find_one({"_id": todo.id})
    if not existing_todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=TODO_NOT_FOUND
        )
    result = request.app.todo.update_one(
        {"_id": todo.id}, {"$set": todo.dict(exclude_unset=True)}
    )
    if result.modified_count == 1:
        return {"message": TODO_UPDATED_SUCCESSFULLY}
    raise HTTPException(status_code=status.HTTP_200_OK, detail=NO_CHANGES)


@router.delete("/{todo_id}")
def delete_todo(todo_id: PyObjectId, request: Request):
    existing_todo = request.app.todo.find_one({"_id": todo_id})

    if not existing_todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=TODO_NOT_FOUND
        )

    result = request.app.todo.delete_one({"_id": todo_id})

    if result.deleted_count == 1:
        return {"message": TODO_DELETED_SUCCESSFULLY}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete todo",
        )
