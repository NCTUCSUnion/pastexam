# utils.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from httpx import AsyncClient
import httpx
from config import settings
from models import UserRoles
from datetime import datetime, timezone
from types import SimpleNamespace

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
        if user_id is None:
            raise credentials_exception
        return UserRoles(user_id=user_id)
    except JWTError:
        raise credentials_exception

# 2. OAuth2 callback (Exchange code for token, get userinfo, and sign JWT)
async def oauth_callback(code: str, state: str = None, stored_state: str = None):
    """
    Verify CSRF token and handle OAuth callback for NYCU OAuth
    """
    if state and stored_state and state != stored_state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
        
    async with httpx.AsyncClient(verify=False) as client:
        token_resp = await client.post(
            settings.OAUTH_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.OAUTH_CLIENT_ID,
                "client_secret": settings.OAUTH_CLIENT_SECRET,
                "redirect_uri": settings.OAUTH_REDIRECT_URI,
            }
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="OAuth token exchange failed")
            
        token_data = token_resp.json()
        access_token = token_data["access_token"]
        
        profile_resp = await client.get(
            settings.OAUTH_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if profile_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Cannot fetch user info")
            
        userinfo = profile_resp.json()
        return {
            "provider": "nycu",
            "sub": userinfo.get("username"),
            "email": userinfo.get("email"),
            "name": userinfo.get("username"),
            "avatar_url": None
        }

from minio import Minio
from datetime import timedelta

_minio_client = None

def get_minio_client() -> Minio:
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )
        if not _minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
            _minio_client.make_bucket(settings.MINIO_BUCKET_NAME)
    return _minio_client

def presigned_put_url(object_name: str, expires: int = 600) -> str:
    """
    Get a presigned PUT URL for frontend to upload PDF files.
    """
    client = get_minio_client()
    return client.presigned_put_object(
        bucket_name=settings.MINIO_BUCKET_NAME,
        object_name=object_name,
        expires=timedelta(seconds=expires)
    )

def presigned_get_url(object_name: str, expires: int = 3600) -> str:
    """
    Get a presigned GET URL for frontend to download/preview PDF files.
    """
    client = get_minio_client()
    return client.presigned_get_object(
        bucket_name=settings.MINIO_BUCKET_NAME,
        object_name=object_name,
        expires=timedelta(seconds=expires)
    )
