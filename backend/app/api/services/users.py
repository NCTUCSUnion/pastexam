from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_session
from app.models.models import (
    User,
    UserCreate,
    UserNicknameUpdate,
    UserPage,
    UserRead,
    UserRoles,
    UserUpdate,
)
from app.utils.auth import get_current_user, get_password_hash

router = APIRouter()

NICKNAME_MAX_LENGTH = 15

# Columns the admin user list can be sorted by
USER_SORT_FIELDS = {
    "name": User.name,
    "email": User.email,
    "is_admin": User.is_admin,
    "is_local": User.is_local,
    "last_login": User.last_login,
}


def _user_order_by(sort: str):
    """Parse "-is_admin,name" into ORDER BY clauses ("-" means descending)."""
    clauses = []
    for part in filter(None, (p.strip() for p in sort.split(","))):
        descending = part.startswith("-")
        column = USER_SORT_FIELDS.get(part.lstrip("-"))
        if column is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot sort by {part.lstrip('-')}",
            )
        clauses.append(
            column.desc().nulls_last() if descending else column.asc().nulls_last()
        )
    # A unique tie-breaker keeps the order stable across pages
    clauses.append(User.id.asc())
    return clauses


@router.get("/admin/users", response_model=UserPage)
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    is_admin: bool | None = None,
    sort: str = Query("-is_admin,name", max_length=200),
    current_user: UserRoles = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    List users one page at a time, with search, filtering and sorting (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    filters = [User.deleted_at.is_(None)]
    if search and search.strip():
        escaped = (
            search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        pattern = f"%{escaped}%"
        filters.append(
            or_(
                User.name.ilike(pattern, escape="\\"),
                User.email.ilike(pattern, escape="\\"),
            )
        )
    if is_admin is not None:
        filters.append(User.is_admin == is_admin)

    order_by = _user_order_by(sort)
    total = await db.scalar(select(func.count()).select_from(User).where(*filters))
    result = await db.execute(
        select(User)
        .where(*filters)
        .order_by(*order_by)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return UserPage(
        items=result.scalars().all(), total=total, page=page, page_size=page_size
    )


@router.post("/admin/users", response_model=UserRead)
async def create_user(
    user_data: UserCreate,
    current_user: UserRoles = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Create a new user (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    result = await db.execute(select(User).where(User.name == user_data.name))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this name already exists",
        )
    hashed_password = get_password_hash(user_data.password)
    user = User(
        name=user_data.name,
        nickname=user_data.name,
        email=user_data.email,
        password_hash=hashed_password,
        is_admin=user_data.is_admin,
        is_local=True,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.get("/me", response_model=UserRead)
async def get_me(
    current_user: UserRoles = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    user = await db.scalar(
        select(User).where(User.id == current_user.user_id, User.deleted_at.is_(None))
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if not user.nickname:
        user.nickname = user.name
        await db.commit()
        await db.refresh(user)
    return user


@router.patch("/me/nickname", response_model=UserRead)
async def update_my_nickname(
    payload: UserNicknameUpdate,
    current_user: UserRoles = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    user = await db.scalar(
        select(User).where(User.id == current_user.user_id, User.deleted_at.is_(None))
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    nickname = (payload.nickname or "").strip()
    if not nickname:
        nickname = user.name
    if len(nickname) > NICKNAME_MAX_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"暱稱超出 {NICKNAME_MAX_LENGTH} 字",
        )

    user.nickname = nickname
    await db.commit()
    await db.refresh(user)
    return user


@router.put("/admin/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: UserRoles = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Update a user (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user_data.name is not None:
        result = await db.execute(
            select(User).where(User.name == user_data.name, User.id != user_id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this name already exists",
            )
        user.name = user_data.name

    if user_data.email is not None:
        result = await db.execute(
            select(User).where(User.email == user_data.email, User.id != user_id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )
        user.email = user_data.email

    if user_data.password is not None:
        user.password_hash = get_password_hash(user_data.password)

    if user_data.is_admin is not None:
        user.is_admin = user_data.is_admin

    await db.commit()
    await db.refresh(user)

    return user


@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: UserRoles = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Delete a user (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    if current_user.user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself"
        )
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.deleted_at = datetime.now(UTC)
    await db.commit()

    return {"detail": "User deleted successfully"}
