import hmac
import logging
import secrets
from datetime import UTC, datetime
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.db.session import get_session
from app.models.models import User
from app.services.auth import oauth_callback
from app.utils.auth import authenticate_user, blacklist_token, get_current_user
from app.utils.jwt import jwt
from app.utils.rate_limit import get_retry_after, record_hit
from app.utils.redis import get_redis

logger = logging.getLogger(__name__)

router = APIRouter()

# The OAuth callback hands the frontend a one-time code instead of the JWT itself,
# so tokens never appear in URLs and a login link only works in the browser that
# started the login (prevents login CSRF with someone else's token).
OAUTH_CODE_TTL_SECONDS = 60
OAUTH_CODE_KEY_PREFIX = "oauth_code:"


class OAuthCodeExchange(BaseModel):
    code: str


def _issue_access_token(user: User) -> str:
    payload = {
        "uid": user.id,
        "email": user.email,
        "name": user.name,
        "is_admin": user.is_admin,
        "exp": int(
            datetime.now(UTC).timestamp() + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        ),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _login_callback_redirect(**params: str) -> RedirectResponse:
    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/login/callback?{urlencode(params)}"
    )


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
):
    """
    Local login endpoint for users with password authentication
    """
    # Count failures per login name; behind the proxy every request shares one IP
    login_key = f"login:{form_data.username.strip().lower()}"
    retry_after = await get_retry_after(login_key, settings.LOGIN_FAILURE_LIMIT)
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts, please try again later",
            headers={"Retry-After": str(retry_after)},
        )

    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        await record_hit(login_key, settings.LOGIN_FAILURE_WINDOW_SECONDS)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last_login timestamp
    user.last_login = datetime.now(UTC)
    await db.commit()
    await db.refresh(user)

    return {"access_token": _issue_access_token(user), "token_type": "bearer"}


@router.get("/oauth/login")
async def oauth_login(request: Request):
    """
    Initialize OAuth login flow
    Supports NYCU OAuth login
    """
    csrf_token = secrets.token_urlsafe(32)
    request.session["csrf_token"] = csrf_token

    auth_params = {
        "client_id": settings.OAUTH_CLIENT_ID,
        "response_type": "code",
        "state": csrf_token,
        "scope": "profile",
        "redirect_uri": settings.OAUTH_REDIRECT_URI,
    }
    auth_url = f"{settings.OAUTH_AUTHORIZE_URL}?{urlencode(auth_params)}"
    return RedirectResponse(url=auth_url)


@router.get("/oauth/callback")
async def auth_callback_endpoint(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_session),
):
    """
    Universal OAuth callback endpoint.
    The browser lands here directly, so every outcome redirects back to the
    frontend, which shows an error message for `?error=`.
    """
    stored_state = request.session.pop("csrf_token", None)
    if error or not code:
        return _login_callback_redirect(error="denied")

    try:
        info = await oauth_callback(code, state, stored_state)
    except HTTPException as exc:
        logger.warning("OAuth callback failed: %s", exc.detail)
        return _login_callback_redirect(
            error="state" if exc.status_code == 400 else "provider"
        )
    if not info.get("sub") or not info.get("email"):
        logger.warning("OAuth provider returned no subject or email")
        return _login_callback_redirect(error="provider")

    now = datetime.now(UTC)

    result = await db.execute(
        select(User).where(
            User.oauth_provider == info["provider"], User.oauth_sub == info["sub"]
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            oauth_provider=info["provider"],
            oauth_sub=info["sub"],
            email=info["email"],
            name=info["name"],
            nickname=info["name"],
            is_local=False,
            last_login=now,
        )
        db.add(user)
        try:
            await db.commit()
        except IntegrityError:
            # Name or email already belongs to another (e.g. local) account
            await db.rollback()
            logger.warning(
                "OAuth user %s conflicts with an existing account", info["sub"]
            )
            return _login_callback_redirect(error="conflict")
        await db.refresh(user)
    elif user.deleted_at is not None:
        return _login_callback_redirect(error="suspended")
    else:
        user.last_login = now
        await db.commit()
        await db.refresh(user)

    exchange_code = secrets.token_urlsafe(32)
    await get_redis().setex(
        f"{OAUTH_CODE_KEY_PREFIX}{exchange_code}",
        OAUTH_CODE_TTL_SECONDS,
        _issue_access_token(user),
    )
    request.session["oauth_code"] = exchange_code
    return _login_callback_redirect(code=exchange_code)


@router.post("/oauth/exchange")
async def oauth_exchange(request: Request, body: OAuthCodeExchange):
    """
    Trade the one-time code from the OAuth callback for an access token.
    Only the browser session that completed the callback can redeem it.
    """
    stored_code = request.session.pop("oauth_code", None)
    if not stored_code or not hmac.compare_digest(stored_code, body.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid login code"
        )
    token = await get_redis().getdel(f"{OAUTH_CODE_KEY_PREFIX}{body.code}")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid login code"
        )
    if isinstance(token, bytes):
        token = token.decode()
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    request: Request,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Logout endpoint that blacklists the current token and updates logout time
    """
    # Update user's last logout time
    result = await db.execute(
        select(User).where(User.id == current_user.user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user:
        user.last_logout = datetime.now(UTC)
        await db.commit()

    # Blacklist the token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        await blacklist_token(token)
    return {"message": "Successfully logged out"}
