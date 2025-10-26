from fastapi import HTTPException
import httpx, hmac
from app.core.config import settings

async def oauth_callback(code: str, state: str = None, stored_state: str = None):
    """
    Verify CSRF token and handle OAuth callback for NYCU OAuth
    """
    if not state or not stored_state or not hmac.compare_digest(state, stored_state):
        raise HTTPException(status_code=400, detail="Invalid state parameter")
        
    try:
        async with httpx.AsyncClient() as client:
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
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Failed to connect to OAuth server: {e}")

    if token_resp.status_code != 200:
        raise HTTPException(status_code=token_resp.status_code, detail="OAuth token exchange failed")
            
    token_data = token_resp.json()
    access_token = token_data["access_token"]
    
    try:
        async with httpx.AsyncClient() as client:
            profile_resp = await client.get(
                settings.OAUTH_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch user info: {e}")

    if profile_resp.status_code != 200:
        raise HTTPException(status_code=profile_resp.status_code, detail="Cannot fetch user info")
        
    userinfo = profile_resp.json()
    return {
        "provider": "nycu",
        "sub": userinfo.get("username"),
        "email": userinfo.get("email"),
        "name": userinfo.get("username"),
        "avatar_url": None
    }
