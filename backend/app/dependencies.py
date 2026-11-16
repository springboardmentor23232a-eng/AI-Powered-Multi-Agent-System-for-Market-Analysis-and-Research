from typing import Tuple
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.revoked_token import RevokedToken
from app.models.user import User
from app.security import decode_access_token, hash_token

# HTTPBearer scheme: enforces Authorization: Bearer <token> header and integrates with Swagger UI
bearer_scheme = HTTPBearer(
    auto_error=True,
    description="JWT Bearer authorization token. Format: Bearer <token>",
)


def get_current_token_payload(
    auth: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Tuple[str, dict]:
    """
    Extracts the Bearer JWT token from the Authorization header,
    decodes its payload, and checks against the PostgreSQL revoked_tokens denylist.
    Rejects missing, forged, expired, or revoked tokens.
    """
    token = auth.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1. Decode & cryptographically verify signature and expiration
    payload = decode_access_token(token)

    # 2. Check if token has been revoked in the database
    jti = payload.get("jti")
    token_hash_val = hash_token(token)

    revocation_filter = (RevokedToken.token_hash == token_hash_val)
    if jti:
        revocation_filter = (RevokedToken.jti == jti) | revocation_filter

    is_revoked = db.query(RevokedToken).filter(revocation_filter).first()
    if is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token, payload


def get_current_user(
    token_and_payload: Tuple[str, dict] = Depends(get_current_token_payload),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency that resolves the authenticated User from a valid, non-revoked Bearer token.
    """
    _, payload = token_and_payload
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing user identifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject format.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    return user
