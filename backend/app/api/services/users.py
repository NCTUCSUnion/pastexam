from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

from app.db.session import get_session
from app.models.models import User, UserRead, UserCreate, UserUpdate, UserRoles
from app.utils.auth import get_current_user, get_password_hash, verify_password

router = APIRouter()

@router.get("/admin/users", response_model=List[UserRead])
async def get_users(
    current_user: UserRoles = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Get all users (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users

@router.post("/admin/users", response_model=UserRead)
async def create_user(
    user_data: UserCreate,
    current_user: UserRoles = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Create a new user (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    result = await db.execute(select(User).where(User.name == user_data.name))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this name already exists"
        )
    hashed_password = get_password_hash(user_data.password)
    user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed_password,
        is_admin=user_data.is_admin,
        is_local=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user

@router.put("/admin/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: UserRoles = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Update a user (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user_data.name is not None:
        result = await db.execute(
            select(User).where(User.name == user_data.name, User.id != user_id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this name already exists"
            )
        user.name = user_data.name
    
    if user_data.email is not None:
        result = await db.execute(
            select(User).where(User.email == user_data.email, User.id != user_id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
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
    db: AsyncSession = Depends(get_session)
):
    """
    Delete a user (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if current_user.user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.delete(user)
    await db.commit()
    
    return {"detail": "User deleted successfully"} 