from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_todo_list():
    return {"test"}
    # Your code to retrieve and return todo list
    pass


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
