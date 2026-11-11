from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserProfileResponse, UserUpdateProfileRequest
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/profile", response_model=UserProfileResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """Fetch current user profile details."""
    return current_user


@router.put("/profile", response_model=UserProfileResponse)
def update_profile(
    req: UserUpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update profile full name."""
    current_user.full_name = req.full_name.strip()
    db.commit()
    db.refresh(current_user)
    return current_user

