"""Business logic for user accounts and preferences."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models import User, UserPreferences
from app.schemas import PreferencesUpdate, UserRegister


class EmailAlreadyRegisteredError(Exception):
    pass


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.strip().lower()))


def register_user(db: Session, data: UserRegister) -> User:
    """Create a user and their default preferences in one transaction."""
    if get_user_by_email(db, data.email) is not None:
        raise EmailAlreadyRegisteredError(data.email)

    user = User(email=data.email, password_hash=hash_password(data.password))
    user.preferences = UserPreferences()
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:  # two simultaneous registrations with the same email
        db.rollback()
        raise EmailAlreadyRegisteredError(data.email) from exc
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return the user if the email/password pair is correct, otherwise None."""
    user = get_user_by_email(db, email)
    if not verify_password(password, user.password_hash if user else None):
        return None
    return user


def get_or_create_preferences(db: Session, user: User) -> UserPreferences:
    if user.preferences is None:
        user.preferences = UserPreferences()
        db.commit()
        db.refresh(user.preferences)
    return user.preferences


def update_preferences(db: Session, user: User, changes: PreferencesUpdate) -> UserPreferences:
    preferences = get_or_create_preferences(db, user)
    for field, value in changes.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(preferences, field, value)
    db.commit()
    db.refresh(preferences)
    return preferences
