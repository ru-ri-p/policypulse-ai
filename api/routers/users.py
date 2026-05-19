# api/routers/users.py
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

from api.auth import get_current_user

router = APIRouter()


class UserProfile(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime | None = None


@router.get("/profile", response_model=UserProfile)
def get_profile(user: dict = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return UserProfile(
        id=user["id"],
        email=user["email"],
        created_at=user["created_at"],
    )
