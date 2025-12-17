from fastapi import APIRouter, Depends

from app.models.user import UserInDB, UserResponse
from app.routers.auth import get_current_active_user

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
    return current_user
