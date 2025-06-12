from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from datetime import datetime, timezone, timedelta
import uuid
import os

from app.db.init_db import get_session
from app.models.models import User, Course, CourseInfo, CoursesByCategory, Archive, ArchiveRead, CourseCategory, ArchiveType
from app.utils.auth import get_current_user
from app.utils.storage import presigned_get_url

router = APIRouter()

@router.get("", response_model=CoursesByCategory)
async def get_categorized_courses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
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

@router.get("/{course_id}/archives", response_model=List[ArchiveRead])
async def get_course_archives(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Get all archives for a specific course.
    """
    course_query = select(Course).where(Course.id == course_id)
    result = await db.execute(course_query)
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with id {course_id} not found"
        )

    query = select(Archive).where(
        Archive.course_id == course_id,
        Archive.deleted_at.is_(None)
    ).order_by(Archive.created_at.desc())
    result = await db.execute(query)
    archives = result.scalars().all()
    
    return archives

@router.get("/{course_id}/archives/{archive_id}/url")
async def get_archive_url(
    course_id: int,
    archive_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Get presigned URLs for downloading and previewing an archive
    """
    query = select(Archive).where(
        Archive.course_id == course_id,
        Archive.id == archive_id,
        Archive.deleted_at.is_(None)
    )
    result = await db.execute(query)
    archive = result.scalar_one_or_none()
    
    if not archive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archive not found"
        )
        
    return {
        "download_url": presigned_get_url(archive.object_name, expires=timedelta(hours=1)),  # 1 hour
        "preview_url": presigned_get_url(archive.object_name, expires=timedelta(minutes=30))  # 30 minutes
    }

@router.patch("/{course_id}/archives/{archive_id}")
async def update_archive(
    course_id: int,
    archive_id: int,
    name: str = Form(None),
    professor: str = Form(None),
    archive_type: ArchiveType = Form(None),
    has_answers: bool = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
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
        Archive.id == archive_id,
        Archive.deleted_at.is_(None)
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

@router.delete("/{course_id}/archives/{archive_id}")
async def delete_archive(
    course_id: int,
    archive_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Soft delete an archive. Users can only delete their own uploads.
    Admins can delete any archive.
    """
    query = select(Archive).where(
        Archive.course_id == course_id,
        Archive.id == archive_id,
        Archive.deleted_at.is_(None)
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

    archive.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    
    return {"message": "Archive deleted successfully"}