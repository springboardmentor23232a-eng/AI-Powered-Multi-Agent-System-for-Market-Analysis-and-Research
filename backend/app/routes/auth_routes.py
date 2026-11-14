from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserPreference
from app.schemas import UserRegister, UserLogin, Token, UserOut
from app.security import hash_password, verify_password, create_access_token
from app.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user:
    1. Validates full name, email, and password matching.
    2. Checks if email is already registered.
    3. Securely hashes password with bcrypt.
    4. Persists user in the database.
    5. Creates default user preferences (NASDAQ, 1 Year).
    """
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    hashed_pw = hash_password(user_in.password)
    new_user = User(
        full_name=user_in.full_name.strip(),
        email=user_in.email,
        password_hash=hashed_pw
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Automatically initialize default preferences
    default_prefs = UserPreference(
        user_id=new_user.user_id,
        market="NASDAQ",
        analysis_period="1 Year"
    )
    db.add(default_prefs)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user credentials and issue signed JWT token.
    Produces clear error message on incorrect credentials.
    """
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT access token with user_id in 'sub' claim
    token = create_access_token(data={"sub": str(user.user_id), "email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve profile and preferences of the currently authenticated user."""
    return current_user
