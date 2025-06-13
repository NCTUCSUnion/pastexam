from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.models import UserRoles, User
from app.db.init_db import AsyncSessionLocal
from sqlalchemy.orm import Session
import redis

redis_client = redis.from_url(settings.REDIS_URL)

oauth2_scheme = HTTPBearer()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def blacklist_token(token: str, expire_seconds: int = 7200):
    redis_client.setex(f"blacklist:{token}", expire_seconds, "1")

def is_token_blacklisted(token: str) -> bool:
    return bool(redis_client.get(f"blacklist:{token}"))

async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserRoles:
    """
    Extract user_id from Bearer <token> in header and verify user's admin status from database.
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

        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise credentials_exception

        return UserRoles(user_id=user_id, is_admin=user.is_admin)
    except JWTError:
        raise credentials_exception 