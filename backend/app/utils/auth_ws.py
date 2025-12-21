from datetime import datetime, timezone

from fastapi import WebSocket
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import User
from app.utils.auth import is_token_blacklisted


def get_ws_token(websocket: WebSocket) -> str | None:
    auth_header = websocket.headers.get("authorization") or ""
    token = None
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()

    if not token:
        token = websocket.query_params.get("token")

    if not token:
        return None

    return token


async def get_ws_token_payload(websocket: WebSocket) -> dict | None:
    token = get_ws_token(websocket)
    if not token:
        return None

    if is_token_blacklisted(token):
        return None

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        exp = payload.get("exp")
        if exp is None or exp < datetime.now(timezone.utc).timestamp():
            return None

        user_id: int | None = payload.get("uid")
        if user_id is None:
            return None

        return payload
    except JWTError:
        return None


async def get_ws_user_id(websocket: WebSocket, db: AsyncSession) -> int | None:
    payload = await get_ws_token_payload(websocket)
    if not payload:
        return None

    user_id: int | None = payload.get("uid")
    if user_id is None:
        return None

    return await db.scalar(
        select(User.id).where(User.id == user_id, User.deleted_at.is_(None))
    )


async def get_ws_user(websocket: WebSocket, db: AsyncSession) -> User | None:
    user_id = await get_ws_user_id(websocket, db)
    if not user_id:
        return None
    return await db.scalar(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
