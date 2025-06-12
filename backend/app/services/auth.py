from fastapi import HTTPException
import httpx
from app.core.config import settings

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