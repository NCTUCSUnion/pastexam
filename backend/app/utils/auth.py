from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timezone

from app.core.config import settings
from app.models.models import UserRoles

oauth2_scheme = HTTPBearer()

async def get_current_user(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> UserRoles:
    """
    Extract user_id from Bearer <token> in header.
    """
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
            options={"verify_signature": False},
        )
        user_id: int = payload.get("uid")
        is_admin: bool = payload.get("is_admin", False)
        if user_id is None:
            raise credentials_exception
        return UserRoles(user_id=user_id, is_admin=is_admin)
    except JWTError:
        raise credentials_exception 