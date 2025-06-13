from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime, timezone
from urllib.parse import urlencode
import secrets

from app.db.init_db import get_session
from app.models.models import User
from app.services.auth import oauth_callback
from app.utils.jwt import jwt
from app.core.config import settings
from app.utils.auth import get_current_user, blacklist_token

router = APIRouter()

@router.get("/login")
async def oauth_login(request: Request):
    """
    Initialize OAuth login flow
    Supports NYCU OAuth login
    """
    csrf_token = secrets.token_urlsafe(32)
    request.session['csrf_token'] = csrf_token
    
    auth_params = {
        "client_id": settings.OAUTH_CLIENT_ID,
        "response_type": "code",
        "state": csrf_token,
        "scope": "profile",
        "redirect_uri": settings.OAUTH_REDIRECT_URI
    }
    auth_url = f"{settings.OAUTH_AUTHORIZE_URL}?{urlencode(auth_params)}"
    return RedirectResponse(url=auth_url)

@router.get("/callback")
async def auth_callback_endpoint(
    request: Request,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_session)
):
    """
    Universal OAuth callback endpoint
    """
    stored_state = request.session.pop('csrf_token', None)
    info = await oauth_callback(code, state, stored_state)
    if not info.get("sub") or not info.get("email"):
        raise HTTPException(status_code=400, detail="Invalid OAuth response")
    
    result = await db.execute(
        select(User).where(
            User.oauth_provider == info["provider"],
            User.oauth_sub == info["sub"]
        )
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        user = User(
            oauth_provider=info["provider"],
            oauth_sub=info["sub"],
            email=info["email"],
            name=info["name"]
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    payload = {
        "uid": user.id,
        "email": user.email,
        "name": user.name,
        "is_admin": user.is_admin,
        "exp": int(datetime.now(timezone.utc).timestamp() + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    frontend_url = settings.FRONTEND_URL
    redirect_url = f"{frontend_url}/login/callback?token={token}"
    return RedirectResponse(url=redirect_url)

@router.post("/logout")
async def logout(
    request: Request,
    current_user = Depends(get_current_user)
):
    """
    Logout endpoint that blacklists the current token
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        blacklist_token(token)
    return {"message": "Successfully logged out"} 