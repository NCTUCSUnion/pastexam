from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_session
from app.models.models import (
    Notification,
    NotificationCreate,
    NotificationRead,
    NotificationUpdate,
    UserRoles,
)
from app.utils.auth import get_current_user

router = APIRouter()


def _apply_time_filters(statement):
    now = datetime.now(timezone.utc)
    return (
        statement.where(Notification.deleted_at.is_(None))
        .where(Notification.is_active.is_(True))
        .where((Notification.starts_at.is_(None)) | (Notification.starts_at <= now))
        .where((Notification.ends_at.is_(None)) | (Notification.ends_at >= now))
    )


@router.get("/active", response_model=List[NotificationRead])
async def get_active_notifications(
    db: AsyncSession = Depends(get_session),
):
    query = select(Notification).order_by(Notification.updated_at.desc())
    query = _apply_time_filters(query)
    result = await db.execute(query)
    notifications = result.scalars().all()
    return [
        NotificationRead.model_validate(notification) for notification in notifications
    ]


@router.get("", response_model=List[NotificationRead])
async def list_public_notifications(
    db: AsyncSession = Depends(get_session),
):
    query = select(Notification).order_by(Notification.updated_at.desc())
    query = _apply_time_filters(query)
    result = await db.execute(query)
    notifications = result.scalars().all()
    return [
        NotificationRead.model_validate(notification) for notification in notifications
    ]


@router.get("/admin/notifications", response_model=List[NotificationRead])
async def list_admin_notifications(
    db: AsyncSession = Depends(get_session),
    current_user: UserRoles = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    query = (
        select(Notification)
        .where(Notification.deleted_at.is_(None))
        .order_by(Notification.updated_at.desc())
    )
    result = await db.execute(query)
    notifications = result.scalars().all()
    return [
        NotificationRead.model_validate(notification) for notification in notifications
    ]


@router.post(
    "/admin/notifications",
    response_model=NotificationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_notification(
    notification_data: NotificationCreate,
    db: AsyncSession = Depends(get_session),
    current_user: UserRoles = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    notification = Notification(**notification_data.model_dump())
    now = datetime.now(timezone.utc)
    notification.created_at = now
    notification.updated_at = now

    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return NotificationRead.model_validate(notification)


@router.put("/admin/notifications/{notification_id}", response_model=NotificationRead)
async def update_notification(
    notification_id: int,
    notification_data: NotificationUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: UserRoles = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id, Notification.deleted_at.is_(None)
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )

    update_data = notification_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(notification, field, value)

    notification.updated_at = datetime.now(timezone.utc)

    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return NotificationRead.model_validate(notification)


@router.delete(
    "/admin/notifications/{notification_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: UserRoles = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id, Notification.deleted_at.is_(None)
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )

    now = datetime.now(timezone.utc)
    notification.deleted_at = now
    notification.updated_at = now
    await db.commit()
