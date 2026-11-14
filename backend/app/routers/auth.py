from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserPreference
from app.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    GoogleLoginRequest,
    UserResponse,
    TokenResponse,
    RegisterResponse,
)
from app.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter()

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account"
)
def register_user(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    User Registration:
    - Validates email and matching passwords.
    - Checks whether the email is already registered in PostgreSQL.
    - Hashes password using bcrypt.
    - Stores the user in the PostgreSQL 'users' table.
    - Initializes default user preferences (market: NSE, period: 1 Year).
    - Returns a success message and safe user details.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already registered. Please log in or use a different email."
        )

    # Hash password securely with bcrypt
    hashed_password = hash_password(request.password)

    # Create new User model instance
    new_user = User(
        full_name=request.full_name,
        email=request.email.lower(),
        password_hash=hashed_password
    )
    db.add(new_user)
    db.flush()  # Populates new_user.user_id

    # Create default user preferences as specified in Module 1
    default_prefs = UserPreference(
        user_id=new_user.user_id,
        market="NSE",
        analysis_period="1 Year"
    )
    db.add(default_prefs)
    db.commit()
    db.refresh(new_user)

    return RegisterResponse(
        message="Registration successful! You can now log in to your research workspace.",
        user=UserResponse.model_validate(new_user)
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and issue JWT token"
)
def login_user(request: UserLoginRequest, db: Session = Depends(get_db)):
    """
    User Login:
    - Verifies user email exists in PostgreSQL.
    - Verifies password against stored bcrypt hash.
    - Issues a signed JWT access token containing user_id and expiration time.
    """
    user = db.query(User).filter(User.email == request.email.lower()).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password. Please check your credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT token
    access_token = create_access_token(data={"sub": str(user.user_id), "email": user.email})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post(
    "/google",
    response_model=TokenResponse,
    summary="One-Click Sign In or Register with Google OAuth"
)
def google_auth(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Seamless Google OAuth sign-in & register:
    - If mode == 'login': Requires the user to exist in PostgreSQL. If not, raises 404.
    - If mode == 'register': Registers new user in PostgreSQL with default preferences if not yet present.
    """
    email_clean = request.email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()
    auth_mode = (request.mode or "login").lower()

    if auth_mode == "login":
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No account found for Google email '{email_clean}'. Please create an account first."
            )
    else:  # 'register' mode
        if not user:
            # Auto-create user from Google OAuth
            hashed = hash_password(f"GoogleOAuthSecureHash_{email_clean}_2026")
            user = User(
                full_name=request.full_name or "Google User",
                email=email_clean,
                password_hash=hashed
            )
            db.add(user)
            db.flush()

            # Create default preferences
            pref = UserPreference(
                user_id=user.user_id,
                market="NSE",
                analysis_period="1 Year"
            )
            db.add(pref)
            db.commit()
            db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.user_id), "email": user.email})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile"
)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Protected endpoint: Derives identity strictly from verified JWT token.
    Returns the authenticated user's profile.
    """
    return UserResponse.model_validate(current_user)

