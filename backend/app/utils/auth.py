from datetime import datetime, timezone

import redis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_session
from app.models.models import User, UserRoles

pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated=["bcrypt"])
redis_client = redis.from_url(settings.REDIS_URL)

oauth2_scheme = HTTPBearer()


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def blacklist_token(token: str, expire_seconds: int = 7200):
    redis_client.setex(f"blacklist:{token}", expire_seconds, "1")


def is_token_blacklisted(token: str) -> bool:
    result = redis_client.get(f"blacklist:{token}")
    return result is not None


async def authenticate_user(name: str, password: str, db: AsyncSession) -> User | None:
    """
    Authenticate a local user with name and password.
    Returns None if authentication fails or if the user is not a local user.
    """
    result = await db.execute(
        select(User).where(User.name == name, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_local:
        return None

    if not user.password_hash:
        return None
    if not verify_password(password, user.password_hash):
        return None

    return user


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_session),
) -> UserRoles:
    """
    Extract user_id from Bearer <token> in header and verify user's admin
    status from database.
    """
    if is_token_blacklisted(token.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been invalidated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Cannot validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        exp = payload.get("exp")
        if exp is None or exp < datetime.now(timezone.utc).timestamp():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id: int = payload.get("uid")
        if user_id is None:
            raise credentials_exception

        result = await db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise credentials_exception

        return UserRoles(user_id=user_id, is_admin=user.is_admin)
    except JWTError:
        raise credentials_exception
