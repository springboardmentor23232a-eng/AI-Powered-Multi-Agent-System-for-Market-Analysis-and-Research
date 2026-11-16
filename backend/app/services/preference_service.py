import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException, status

from app.models.user_preference import UserPreference
from app.schemas.preference import PreferenceUpdate

logger = logging.getLogger("uvicorn.error")

DEFAULT_MARKET = "NSE"
DEFAULT_ANALYSIS_PERIOD = "1mo"


def get_or_create_user_preference(db: Session, user_id: int) -> UserPreference:
    """
    Retrieves the user's preference record.
    If none exists, initializes and persists default preferences (NSE, 1mo).
    Guarantees that repeated calls do not create duplicate records.
    """
    try:
        pref = (
            db.query(UserPreference)
            .filter(UserPreference.user_id == user_id)
            .first()
        )
        if pref:
            return pref

        # Initialize defaults for new user
        new_pref = UserPreference(
            user_id=user_id,
            market=DEFAULT_MARKET,
            analysis_period=DEFAULT_ANALYSIS_PERIOD,
        )
        db.add(new_pref)
        db.commit()
        db.refresh(new_pref)
        logger.info(f"Initialized default preferences for user #{user_id}: market={DEFAULT_MARKET}, period={DEFAULT_ANALYSIS_PERIOD}")
        return new_pref
    except IntegrityError:
        db.rollback()
        # Handle concurrent creation race condition gracefully
        pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if pref:
            return pref
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve or create user preferences.",
        )
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(f"Database error in get_or_create_user_preference for user #{user_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while loading preferences.",
        )


def update_user_preference(
    db: Session,
    user_id: int,
    request: PreferenceUpdate,
) -> UserPreference:
    """
    Updates the market and analysis period for the authenticated user.
    Creates the record if it does not already exist.
    Updates the updated_at timestamp and commits to PostgreSQL.
    """
    try:
        pref = (
            db.query(UserPreference)
            .filter(UserPreference.user_id == user_id)
            .first()
        )

        now = datetime.now(timezone.utc)
        if not pref:
            pref = UserPreference(
                user_id=user_id,
                market=request.market,
                analysis_period=request.analysis_period,
                updated_at=now,
            )
            db.add(pref)
        else:
            pref.market = request.market
            pref.analysis_period = request.analysis_period
            pref.updated_at = now

        db.commit()
        db.refresh(pref)
        logger.info(
            f"Updated preferences for user #{user_id}: market='{pref.market}', "
            f"analysis_period='{pref.analysis_period}', updated_at={pref.updated_at}"
        )
        return pref
    except IntegrityError as exc:
        db.rollback()
        logger.error(f"Integrity error updating preferences for user #{user_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflict updating user preferences.",
        )
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(f"Database error in update_user_preference for user #{user_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while updating preferences.",
        )
