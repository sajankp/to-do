from typing import List

from fastapi import APIRouter, Request
from models.todo import Todo

router = APIRouter()


@router.get("/", response_model=List[Todo])
def get_todo_list(request: Request):
    books = list(request.app.todo.find().limit(100))
    return books
    


@router.post("/")
def create_todo():
    # Your code to create a new todo
    pass


@router.put("/{todo_id}")
def update_todo(todo_id: str):
    # Your code to update a todo
    pass


@router.delete("/{todo_id}")
def delete_todo(todo_id: str):
    # Your code to delete a todo
    pass
