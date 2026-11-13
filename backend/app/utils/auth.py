import asyncio
import base64
import hashlib
import hmac
import re
from datetime import UTC, datetime

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_session
from app.models.models import User, UserRoles
from app.utils.activity import record_activity
from app.utils.redis import get_redis

# Hashes use passlib's bcrypt_sha256 v2 format so existing rows keep verifying:
# bcrypt(base64(hmac_sha256(key=salt, msg=password)), salt, rounds).
# Older v1 bcrypt_sha256 and plain bcrypt hashes are still accepted on verify.
_BCRYPT_SHA256_ROUNDS = 12
_BCRYPT_SHA256_V2 = re.compile(
    r"^\$bcrypt-sha256\$v=2,t=(?P<ident>2b),r=(?P<rounds>\d{1,2})"
    r"\$(?P<salt>[^$]{22})\$(?P<digest>[^$]{31})$"
)
_BCRYPT_SHA256_V1 = re.compile(
    r"^\$bcrypt-sha256\$(?P<ident>2[ab]),(?P<rounds>\d{1,2})"
    r"\$(?P<salt>[^$]{22})\$(?P<digest>[^$]{31})$"
)
_BCRYPT_MAX_BYTES = 72

oauth2_scheme = HTTPBearer()


def _hmac_key(password: bytes, salt: str) -> bytes:
    return base64.b64encode(
        hmac.new(salt.encode("ascii"), password, hashlib.sha256).digest()
    )


def get_password_hash(password: str) -> str:
    config = bcrypt.gensalt(rounds=_BCRYPT_SHA256_ROUNDS, prefix=b"2b").decode("ascii")
    salt = config[-22:]
    hashed = bcrypt.hashpw(
        _hmac_key(password.encode("utf-8"), salt), config.encode("ascii")
    )
    digest = hashed.decode("ascii")[-31:]
    return f"$bcrypt-sha256$v=2,t=2b,r={_BCRYPT_SHA256_ROUNDS}${salt}${digest}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    secret = plain_password.encode("utf-8")
    try:
        if match := _BCRYPT_SHA256_V2.match(hashed_password):
            key = _hmac_key(secret, match["salt"])
        elif match := _BCRYPT_SHA256_V1.match(hashed_password):
            key = base64.b64encode(hashlib.sha256(secret).digest())
        else:
            return bcrypt.checkpw(
                secret[:_BCRYPT_MAX_BYTES], hashed_password.encode("ascii")
            )
        rounds = int(match["rounds"])
        bcrypt_hash = f"${match['ident']}${rounds:02d}${match['salt']}{match['digest']}"
        return bcrypt.checkpw(key, bcrypt_hash.encode("ascii"))
    except ValueError:
        return False


def _seconds_until_expiry(token: str) -> int:
    """Seconds left on a token, so a blacklist entry lives exactly as long as it."""
    try:
        exp = jwt.decode(token, options={"verify_signature": False}).get("exp")
    except PyJWTError:
        exp = None
    if exp is None:
        return settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return max(int(exp - datetime.now(UTC).timestamp()), 1)


async def blacklist_token(token: str, expire_seconds: int | None = None):
    if expire_seconds is None:
        expire_seconds = _seconds_until_expiry(token)
    await get_redis().setex(f"blacklist:{token}", expire_seconds, "1")


async def is_token_blacklisted(token: str) -> bool:
    result = await get_redis().get(f"blacklist:{token}")
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
    # bcrypt takes a few hundred ms; keep it off the event loop
    if not await asyncio.to_thread(verify_password, password, user.password_hash):
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
    if await is_token_blacklisted(token.credentials):
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
        if exp is None or exp < datetime.now(UTC).timestamp():
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

        await record_activity(user_id)
        return UserRoles(user_id=user_id, is_admin=user.is_admin)
    except PyJWTError:
        raise credentials_exception
