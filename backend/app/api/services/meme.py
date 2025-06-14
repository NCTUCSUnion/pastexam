from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlalchemy import func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.init_db import get_session
from app.models.models import Meme, MemeRead

router = APIRouter()

@router.get("/", response_model=MemeRead)
async def get_random_meme(
    db: AsyncSession = Depends(get_session),
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