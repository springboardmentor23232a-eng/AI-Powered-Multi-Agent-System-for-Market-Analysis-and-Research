import os
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import RegisterIn, LoginIn, UserOut
from ..security import hash_password, verify_password, create_access_token, EXPIRE_MINUTES
from ..deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

@router.post("/register", status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="This email is already registered.")
    user = User(full_name=data.full_name.strip(), email=email,
                password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    return {"message": "Registration successful. Please sign in."}

@router.post("/login", response_model=UserOut)
def login(data: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not verify_password(data.password, user.password_hash):
        # same message for both cases, so attackers can't find which emails exist
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = create_access_token(user.user_id)
    response.set_cookie(
        key="access_token", value=token,
        httponly=True, secure=COOKIE_SECURE, samesite="lax",
        max_age=EXPIRE_MINUTES * 60,
    )
    return user

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out."}

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user