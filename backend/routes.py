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
import uuid
import os

from db import get_db
from models import (
    User, UserRoles, Meme, MemeRead, Course, CourseCategory, CourseInfo, CoursesByCategory, Archive, ArchiveRead, ArchiveType
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
        "is_admin": user.is_admin,
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
    current_user: UserRoles = Depends(get_current_user),
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
    current_user: UserRoles = Depends(get_current_user),
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

@router.get("/courses/{course_id}/archives/{archive_id}/url")
async def get_archive_url(
    course_id: int,
    archive_id: int,
    current_user: UserRoles = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get presigned URLs for downloading and previewing an archive
    """
    query = select(Archive).where(
        Archive.course_id == course_id,
        Archive.id == archive_id
    )
    result = await db.execute(query)
    archive = result.scalar_one_or_none()
    
    if not archive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archive not found"
        )
        
    return {
        "download_url": presigned_get_url(archive.object_name, expires=3600),  # 1 hour
        "preview_url": presigned_get_url(archive.object_name, expires=1800)  # 30 minutes
    }

@router.post("/archives/upload")
async def upload_archive(
    file: UploadFile,
    subject: str = Form(...),
    category: CourseCategory = Form(...),
    professor: str = Form(...),
    archive_type: str = Form(...),
    has_answers: bool = Form(False),
    filename: str = Form(...),
    academic_year: int = Form(...),
    current_user: UserRoles = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a new archive and create course if not exists
    """
    # First check if user exists
    user_query = select(User).where(User.id == current_user.user_id)
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    query = select(Course).where(
        Course.name == subject,
        Course.category == category
    )
    result = await db.execute(query)
    course = result.scalar_one_or_none()
    
    if not course:
        course = Course(
            name=subject,
            category=category
        )
        db.add(course)
        await db.commit()
        await db.refresh(course)

    _, file_extension = os.path.splitext(file.filename)
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    object_name = f"archives/{course.id}/{unique_filename}"

    archive = Archive(
        course_id=course.id,
        name=filename,
        professor=professor,
        archive_type=archive_type,
        has_answers=has_answers,
        object_name=object_name,
        academic_year=academic_year,
        uploader_id=current_user.user_id
    )
    
    db.add(archive)
    await db.commit()
    await db.refresh(archive)

    upload_url = presigned_put_url(object_name)
    
    return {
        "upload_url": upload_url,
        "archive": {
            "id": archive.id,
            "name": archive.name,
            "professor": archive.professor,
            "archive_type": archive.archive_type,
            "has_answers": archive.has_answers,
            "created_at": archive.created_at,
        }
    }

@router.delete("/courses/{course_id}/archives/{archive_id}")
async def delete_archive(
    course_id: int,
    archive_id: int,
    current_user: UserRoles = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an archive. Users can only delete their own uploads.
    Admins can delete any archive.
    """
    query = select(Archive).where(
        Archive.course_id == course_id,
        Archive.id == archive_id
    )
    result = await db.execute(query)
    archive = result.scalar_one_or_none()
    
    if not archive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archive not found"
        )

    if not current_user.is_admin and archive.uploader_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this archive"
        )

    try:
        # Add your storage deletion logic here
        # Example: await storage.delete_file(archive.object_name)
        pass
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file from storage"
        )

    await db.delete(archive)
    await db.commit()
    
    return {"message": "Archive deleted successfully"}

@router.patch("/courses/{course_id}/archives/{archive_id}")
async def update_archive(
    course_id: int,
    archive_id: int,
    name: str = Form(None),
    professor: str = Form(None),
    archive_type: ArchiveType = Form(None),
    has_answers: bool = Form(None),
    current_user: UserRoles = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update archive information. Only admins can update archives.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update archives"
        )

    query = select(Archive).where(
        Archive.course_id == course_id,
        Archive.id == archive_id
    )
    result = await db.execute(query)
    archive = result.scalar_one_or_none()
    
    if not archive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archive not found"
        )

    if name is not None:
        archive.name = name
    if professor is not None:
        archive.professor = professor
    if archive_type is not None:
        archive.archive_type = archive_type
    if has_answers is not None:
        archive.has_answers = has_answers

    archive.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(archive)
    
    return archive
