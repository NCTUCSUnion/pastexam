from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from datetime import datetime, timezone, timedelta
import uuid
import os

from app.db.init_db import get_session
from app.models.models import User, Course, Archive, ArchiveRead, CourseCategory, ArchiveType
from app.utils.auth import get_current_user
from app.utils.storage import presigned_put_url
from app.core.config import settings
from pydantic import BaseModel

class ArchiveUrlResponse(BaseModel):
    download_url: str
    preview_url: str

router = APIRouter()

@router.post("/upload")
async def upload_archive(
    file: UploadFile,
    subject: str = Form(...),
    category: CourseCategory = Form(...),
    professor: str = Form(...),
    archive_type: str = Form(...),
    has_answers: bool = Form(False),
    filename: str = Form(...),
    academic_year: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Upload a new archive and create course if not exists
    """
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
        Course.category == category,
        Course.deleted_at.is_(None)
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

    upload_url = presigned_put_url(
        object_name=object_name,
        expires=timedelta(hours=1)
    )
    
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