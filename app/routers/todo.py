from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from app.models.todo import PyObjectId, Todo, TodoBase, TodoUpdate
from app.utils.constants import (
    FAILED_CREATE_TODO,
    FAILED_DELETE_TODO,
    NO_CHANGES,
    TODO_DELETED_SUCCESSFULLY,
    TODO_NOT_FOUND,
    TODO_UPDATED_SUCCESSFULLY,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
router = APIRouter(dependencies=[Depends(oauth2_scheme)])


@router.get("/", response_model=List[Todo])
def get_todo_list(request: Request):
    todos = list(request.app.todo.find({"user_id": request.state.user_id}).limit(100))
    return todos


@router.get("/{todo_id}", response_model=Todo)
def get_todo(todo_id: PyObjectId, request: Request):
    todo = request.app.todo.find_one({"_id": todo_id})
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=TODO_NOT_FOUND
        )
    return todo


@router.post("/", response_model=Todo)
def create_todo(request: Request, todo: TodoBase):
    current_time = datetime.now(timezone.utc)

    new_todo = Todo(
        title=todo.title,
        description=todo.description,
        due_date=todo.due_date,
        priority=todo.priority,
        created_at=current_time,
        updated_at=current_time,
        user_id=request.state.user_id,
    )
    result = request.app.todo.insert_one(new_todo.dict())
    if result.acknowledged:
        new_todo.id = result.inserted_id
        return new_todo
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=FAILED_CREATE_TODO,
        )


def are_objects_equal(obj1, obj2):
    if isinstance(obj1, datetime) and isinstance(obj2, datetime):
        # If both objects are datetime objects, handle timezone comparison
        return obj1.replace(tzinfo=timezone.utc) == obj2.replace(tzinfo=timezone.utc)
    else:
        return obj1 == obj2


@router.put("/{todo_id}")
def update_todo(todo: TodoUpdate, request: Request):
    existing_todo = request.app.todo.find_one({"_id": todo.id})
    if not existing_todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=TODO_NOT_FOUND
        )
    todo_dict = todo.dict()
    if any(
        not are_objects_equal(existing_todo[key], todo_dict[key])
        for key in ["title", "description", "due_date", "priority"]
    ):
        updated_todo = todo.dict(exclude_unset=True)
        updated_todo["updated_at"] = datetime.now(timezone.utc)
        result = request.app.todo.update_one(
            {"_id": todo.id},
            {"$set": updated_todo},
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
            detail=FAILED_DELETE_TODO,
        )
