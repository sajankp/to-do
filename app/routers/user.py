from fastapi import APIRouter, Depends, Request

from app.models.user import UserInDB, UserResponse
from app.routers.auth import get_authenticated_user

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def read_users_me(request: Request, current_user: UserInDB = Depends(get_authenticated_user)):
    return current_user
