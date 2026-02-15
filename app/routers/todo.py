from datetime import UTC, datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.models.todo import CreateTodo, PyObjectId, TodoInDB, TodoResponse, TodoUpdate
from app.routers.auth import get_authenticated_user
from app.utils.constants import (
    FAILED_CREATE_TODO,
    FAILED_DELETE_TODO,
    NO_CHANGES,
    TODO_DELETED_SUCCESSFULLY,
    TODO_NOT_FOUND,
)
from app.utils.metrics import (
    TODOS_COMPLETED_TOTAL,
    TODOS_CREATED_TOTAL,
    TODOS_DELETED_TOTAL,
)

router = APIRouter(dependencies=[Depends(get_authenticated_user)])


@router.get("/", response_model=list[TodoResponse])
def get_todo_list(request: Request):
    todos = list(request.app.todo.find({"user_id": request.state.user_id}).limit(100))
    todos = [TodoResponse.from_db(TodoInDB(**todo)) for todo in todos]
    return todos


@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: PyObjectId, request: Request):
    todo = request.app.todo.find_one({"_id": todo_id, "user_id": request.state.user_id})
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TODO_NOT_FOUND)
    return TodoResponse.from_db(TodoInDB(**todo))


@router.post("/", response_model=TodoResponse)
def create_todo(request: Request, todo: CreateTodo):
    new_todo = TodoInDB(
        user_id=PyObjectId(request.state.user_id),
        **todo.model_dump(),
    )

    todo_dict = new_todo.model_dump(by_alias=True, exclude={"id"})

    result = request.app.todo.insert_one(todo_dict)

    if result.acknowledged:
        new_todo.id = result.inserted_id
        TODOS_CREATED_TOTAL.inc()
        return TodoResponse.from_db(new_todo)
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=FAILED_CREATE_TODO,
        )


@router.patch("/{todo_id}", response_model=TodoResponse)
def update_todo(
    todo_id: str,
    todo_update: TodoUpdate,
    request: Request,
):
    existing_todo = request.app.todo.find_one({"_id": ObjectId(todo_id)})
    user_id = request.state.user_id
    if not existing_todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TODO_NOT_FOUND)

    if str(existing_todo.get("user_id")) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this todo",
        )

    update_data = todo_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=NO_CHANGES)

    update_data["updatedAt"] = datetime.now(UTC)

    result = request.app.todo.update_one({"_id": ObjectId(todo_id)}, {"$set": update_data})

    if result.modified_count == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=NO_CHANGES)

    # Only increment completed metric if state changed from incomplete to complete
    if update_data.get("completed") is True and not existing_todo.get("completed"):
        TODOS_COMPLETED_TOTAL.inc()

    updated_todo = request.app.todo.find_one({"_id": ObjectId(todo_id)})
    todo_db = TodoInDB(**updated_todo)

    return TodoResponse.from_db(todo_db)


@router.delete("/{todo_id}")
def delete_todo(todo_id: PyObjectId, request: Request):
    existing_todo = request.app.todo.find_one({"_id": todo_id, "user_id": request.state.user_id})

    if not existing_todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TODO_NOT_FOUND)

    result = request.app.todo.delete_one({"_id": todo_id, "user_id": request.state.user_id})

    if result.deleted_count == 1:
        TODOS_DELETED_TOTAL.inc()
        return {"message": TODO_DELETED_SUCCESSFULLY}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=FAILED_DELETE_TODO,
        )
