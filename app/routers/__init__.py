from fastapi import APIRouter

from routers.todo import router as todo_router

router = APIRouter()

router.include_router(todo_router, prefix="/todo", tags=["todo"])
