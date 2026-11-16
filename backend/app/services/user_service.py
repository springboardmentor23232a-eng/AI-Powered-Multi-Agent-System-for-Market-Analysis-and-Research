import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.auth import UserRegisterRequest, UserLoginRequest
from app.services.security import hash_password, verify_password

logger = logging.getLogger("uvicorn.error")


def register_new_user(db: Session, request: UserRegisterRequest) -> User:
    """
    Registers a new user into the database:
    1. Checks if the normalized email already exists.
    2. Hashes the plain-text password using bcrypt.
    3. Persists the user record into the 'users' table.
    4. Handles database exceptions cleanly and securely.
    """
    clean_email = request.email.strip().lower()

    # 1. Check for existing user by email
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        logger.warning(f"Registration conflict: email '{clean_email}' already exists.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists. Please sign in or use a different email."
        )

    # 2. Hash password securely
    hashed_password = hash_password(request.password)

    # 3. Create new User entity
    new_user = User(
        full_name=request.full_name.strip(),
        email=clean_email,
        password_hash=hashed_password,
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User created successfully: ID {new_user.user_id}, email '{clean_email}'")
        return new_user
    except IntegrityError as exc:
        db.rollback()
        logger.error(f"IntegrityError during user registration: {exc}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists."
        )
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(f"Database error during user registration: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while creating your account. Please try again later."
        )


def authenticate_user(db: Session, request: UserLoginRequest) -> User:
    """
    Authenticates a user against the database:
    1. Finds user by lowercase email.
    2. Verifies the password using bcrypt.
    3. Returns the user object on success; raises 401 Unauthorized otherwise.
    """
    clean_email = request.email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()

    if not user:
        logger.warning(f"Login failed: email '{clean_email}' not found.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials and try again.",
        )

    if not verify_password(request.password, user.password_hash):
        logger.warning(f"Login failed: incorrect password for email '{clean_email}'.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials and try again.",
        )

    logger.info(f"User authenticated successfully: ID {user.user_id}, email '{clean_email}'")
    return user
