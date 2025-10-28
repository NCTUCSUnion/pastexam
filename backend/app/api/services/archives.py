from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import uuid
import os
import io

from app.db.session import get_session
from app.models.models import User, Course, Archive, CourseCategory
from app.utils.auth import get_current_user
from app.utils.storage import get_minio_client
from app.core.config import settings

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

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )

    file_content = await file.read()
    file_size = len(file_content)

    max_size = 10 * 1024 * 1024  # 10MB
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10MB limit"
        )

    _, file_extension = os.path.splitext(file.filename)
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    object_name = f"archives/{course.id}/{unique_filename}"

    try:
        minio_client = get_minio_client()
        file_data = io.BytesIO(file_content)

        minio_client.put_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_name,
            data=file_data,
            length=file_size,
            content_type="application/pdf"
        )

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
                "file_size": file_size
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
