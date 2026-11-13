import asyncio
import io
import logging
import os
import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.db.session import get_session
from app.models.models import Archive, ArchiveType, Course, CourseCategory, User
from app.utils.auth import get_current_user
from app.utils.names import find_course, require_name
from app.utils.rate_limit import get_retry_after, record_hit
from app.utils.storage import get_storage_client

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@router.post("/upload")
async def upload_archive(
    file: UploadFile,
    subject: str = Form(...),
    category: CourseCategory = Form(...),
    professor: str = Form(...),
    archive_type: ArchiveType = Form(...),
    has_answers: bool = Form(False),
    filename: str = Form(...),
    academic_year: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Upload a new archive and create course if not exists
    """
    user_query = select(User).where(
        User.id == current_user.user_id, User.deleted_at.is_(None)
    )
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Admins upload in bulk, so only regular users are limited
    upload_key = f"upload:{current_user.user_id}"
    if not current_user.is_admin:
        retry_after = await get_retry_after(upload_key, settings.UPLOAD_LIMIT_PER_HOUR)
        if retry_after is not None:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Upload limit reached, please try again later",
                headers={"Retry-After": str(retry_after)},
            )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed"
        )

    subject = require_name(subject, "Course name")
    professor = require_name(professor, "Professor")
    filename = require_name(filename, "Archive name")

    file_content = await file.read()
    file_size = len(file_content)

    if file_size > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10MB limit",
        )
    # The PDF header may follow some junk bytes, but must be near the start
    if b"%PDF-" not in file_content[:1024]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File is not a valid PDF"
        )

    course = await find_course(db, subject, category)
    if not course:
        # Flush only to get an id; the course is committed together with the archive
        course = Course(name=subject, category=category)
        db.add(course)
        await db.flush()

    _, file_extension = os.path.splitext(file.filename)
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    object_name = f"archives/{course.id}/{unique_filename}"

    # Count the attempt before writing to storage, so failing uploads cannot be
    # repeated without limit (each one could leave a file behind).
    if not current_user.is_admin:
        await record_hit(upload_key, 60 * 60)

    stored = False
    try:
        storage_client = await asyncio.to_thread(get_storage_client)
        file_data = io.BytesIO(file_content)

        await asyncio.to_thread(
            storage_client.put_object,
            bucket_name=settings.RUSTFS_BUCKET_NAME,
            object_name=object_name,
            data=file_data,
            length=file_size,
            content_type="application/pdf",
        )
        stored = True

        archive = Archive(
            course_id=course.id,
            name=filename,
            professor=professor,
            archive_type=archive_type,
            has_answers=has_answers,
            object_name=object_name,
            academic_year=academic_year,
            uploader_id=current_user.user_id,
        )

        db.add(archive)
        await db.commit()
        await db.refresh(archive)

        return {
            "success": True,
            "message": "File uploaded successfully",
            "archive": {
                "id": archive.id,
                "name": archive.name,
                "professor": archive.professor,
                "archive_type": archive.archive_type,
                "has_answers": archive.has_answers,
                "created_at": archive.created_at,
                "file_size": file_size,
            },
        }

    except HTTPException:
        raise
    # Storage and database failures both end up here
    except Exception:
        logger.exception("Failed to upload archive %s", object_name)
        await db.rollback()
        if stored:
            await _remove_orphan(storage_client, object_name)
        # Details stay in the log: database errors include SQL and parameters
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file",
        )


async def _remove_orphan(storage_client, object_name: str) -> None:
    """Delete a stored file whose database row could not be written."""
    try:
        await asyncio.to_thread(
            storage_client.remove_object,
            bucket_name=settings.RUSTFS_BUCKET_NAME,
            object_name=object_name,
        )
    except Exception:
        logger.warning(
            "Could not remove orphaned upload %s", object_name, exc_info=True
        )
