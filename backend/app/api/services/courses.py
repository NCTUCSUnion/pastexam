from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from datetime import datetime, timezone, timedelta
import uuid
import os

from app.db.init_db import get_session
from app.models.models import User, Course, CourseInfo, CoursesByCategory, Archive, ArchiveRead, CourseCategory, ArchiveType, CourseCreate, CourseUpdate, CourseRead, ArchiveUpdateCourse
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
    is_download: bool = False,
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
    
    if is_download:
        archive.download_count += 1
        await db.commit()
        await db.refresh(archive)
        
    return {
        "download_url": presigned_get_url(archive.object_name, expires=timedelta(hours=1)),
        "preview_url": presigned_get_url(archive.object_name, expires=timedelta(minutes=30))
    }

@router.patch("/{course_id}/archives/{archive_id}")
async def update_archive(
    course_id: int,
    archive_id: int,
    name: str = Form(None),
    professor: str = Form(None),
    archive_type: ArchiveType = Form(None),
    has_answers: bool = Form(None),
    academic_year: int = Form(None),
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
    if academic_year is not None:
        archive.academic_year = academic_year

    archive.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(archive)
    
    return archive


@router.patch("/{course_id}/archives/{archive_id}/course")
async def update_archive_course(
    course_id: int,
    archive_id: int,
    course_update: ArchiveUpdateCourse,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Update archive's course. Only admins can change archive's course.
    Supports both transferring to existing course by ID or creating new course by name and category.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can change archive's course"
        )

    archive_query = select(Archive).where(
        Archive.course_id == course_id,
        Archive.id == archive_id,
        Archive.deleted_at.is_(None)
    )
    archive_result = await db.execute(archive_query)
    archive = archive_result.scalar_one_or_none()
    
    if not archive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archive not found"
        )

    # Determine target course
    new_course = None
    
    if course_update.course_id:
        # Check if trying to transfer to the same course
        if course_update.course_id == course_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot transfer archive to the same course"
            )
            
        # Transfer to existing course by ID
        new_course_query = select(Course).where(Course.id == course_update.course_id)
        new_course_result = await db.execute(new_course_query)
        new_course = new_course_result.scalar_one_or_none()
        
        if not new_course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target course not found"
            )
    elif course_update.course_name and course_update.course_category:
        # Transfer to course by name and category, create if not exists
        new_course_query = select(Course).where(
            Course.name == course_update.course_name,
            Course.category == course_update.course_category
        )
        new_course_result = await db.execute(new_course_query)
        new_course = new_course_result.scalar_one_or_none()
        
        if new_course:
            # Check if trying to transfer to the same course
            if new_course.id == course_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot transfer archive to the same course"
                )
        else:
            # Create new course if it doesn't exist
            new_course = Course(
                name=course_update.course_name,
                category=course_update.course_category
            )
            db.add(new_course)
            await db.commit()
            await db.refresh(new_course)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either course_id or both course_name and course_category must be provided"
        )
    
    archive.course_id = new_course.id
    archive.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(archive)
    
    return {
        "message": f"Archive moved to course '{new_course.name}'",
        "archive_id": archive.id,
        "old_course_id": course_id,
        "new_course_id": new_course.id
    }

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



@router.post("/admin/courses", response_model=CourseRead)
async def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Create a new course. Only admins can create courses.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create courses"
        )

    query = select(Course).where(
        Course.name == course_data.name,
        Course.category == course_data.category
    )
    result = await db.execute(query)
    existing_course = result.scalar_one_or_none()
    
    if existing_course:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course with this name and category already exists"
        )

    course = Course(
        name=course_data.name,
        category=course_data.category
    )
    
    db.add(course)
    await db.commit()
    await db.refresh(course)
    
    return course

@router.put("/admin/courses/{course_id}", response_model=CourseRead)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Update a course. Only admins can update courses.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update courses"
        )

    query = select(Course).where(Course.id == course_id)
    result = await db.execute(query)
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    if course_data.name is not None or course_data.category is not None:
        new_name = course_data.name if course_data.name is not None else course.name
        new_category = course_data.category if course_data.category is not None else course.category
        
        if new_name != course.name or new_category != course.category:
            check_query = select(Course).where(
                Course.name == new_name,
                Course.category == new_category,
                Course.id != course_id
            )
            check_result = await db.execute(check_query)
            existing_course = check_result.scalar_one_or_none()
            
            if existing_course:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Course with this name and category already exists"
                )
    if course_data.name is not None:
        course.name = course_data.name
    if course_data.category is not None:
        course.category = course_data.category
    
    await db.commit()
    await db.refresh(course)
    
    return course

@router.delete("/admin/courses/{course_id}")
async def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Delete a course. Only admins can delete courses.
    This will also soft delete all associated archives.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete courses"
        )

    query = select(Course).where(Course.id == course_id)
    result = await db.execute(query)
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    archives_query = select(Archive).where(
        Archive.course_id == course_id,
        Archive.deleted_at.is_(None)
    )
    archives_result = await db.execute(archives_query)
    archives = archives_result.scalars().all()
    
    current_time = datetime.now(timezone.utc)
    for archive in archives:
        archive.deleted_at = current_time
    await db.delete(course)
    await db.commit()
    
    return {"message": f"Course '{course.name}' and {len(archives)} associated archives deleted successfully"}

@router.get("/admin/courses", response_model=List[CourseRead])
async def list_all_courses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Get all courses with full details. Only admins can access this.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access all courses"
        )

    query = select(Course).order_by(Course.category, Course.name)
    result = await db.execute(query)
    courses = result.scalars().all()
    
    return courses