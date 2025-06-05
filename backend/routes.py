# routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, UploadFile, Form
from fastapi.responses import RedirectResponse
from sqlmodel import select
from sqlalchemy import func 
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional
from datetime import datetime, timezone
from urllib.parse import urlencode
import secrets

from db import get_db
from models import (
    User, Meme, MemeRead, Course, CourseCategory, CourseInfo, CoursesByCategory, Archive, ArchiveRead
)
from utils import get_current_user, oauth_callback, presigned_put_url, presigned_get_url
from utils import jwt

from config import settings

router = APIRouter()

@router.get("/oauth/login")
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

@router.get("/oauth/callback")
async def auth_callback_endpoint(
    request: Request,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db)
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
            name=info.get("name")
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    payload = {
        "uid": user.id,
        "email": user.email,
        "name": user.name,
        "exp": int(datetime.now(timezone.utc).timestamp() + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
        "iat": int(datetime.now(timezone.utc).timestamp())
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    frontend_url = settings.FRONTEND_URL
    redirect_url = f"{frontend_url}/login/callback?token={token}"
    return RedirectResponse(url=redirect_url)

@router.get("/meme", response_model=MemeRead)
async def get_random_meme(
    db: AsyncSession = Depends(get_db),
):
    """
    Get a random meme.
    """
    query = select(Meme).order_by(func.random()).limit(1)
    result = await db.execute(query)
    meme = result.scalar_one_or_none()
    
    if not meme:
        raise HTTPException(status_code=404, detail="No memes available")
    
    return meme

@router.get("/courses", response_model=CoursesByCategory)
async def get_categorized_courses(
    db: AsyncSession = Depends(get_db),
):
    """
    Get all courses grouped by category.
    Returns courses with their IDs grouped by category.
    """
    query = select(Course)
    result = await db.execute(query)
    courses = result.scalars().all()
    
    categorized_courses = CoursesByCategory()
    for course in courses:
        course_info = CourseInfo(id=course.id, name=course.name)
        getattr(categorized_courses, course.category).append(course_info)
    
    return categorized_courses

@router.get("/courses/{course_id}/archives", response_model=List[ArchiveRead])
async def get_course_archives(
    course_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all archives for a specific course
    """
    course_query = select(Course).where(Course.id == course_id)
    course_result = await db.execute(course_query)
    course = course_result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with id {course_id} not found"
        )

    query = select(Archive).where(Archive.course_id == course_id).order_by(Archive.created_at.desc())
    result = await db.execute(query)
    archives = result.scalars().all()
    
    return archives
