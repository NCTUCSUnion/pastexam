import json
import logging

from fastapi import APIRouter, Depends
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_session
from app.models.models import Archive, Course, User
from app.utils.activity import count_active_today, count_online_users
from app.utils.redis import get_redis

router = APIRouter()
logger = logging.getLogger(__name__)

CACHE_KEY = "stats:summary"
CACHE_TTL_SECONDS = 60

EMPTY_STATISTICS = {
    "totalUsers": 0,
    "totalDownloads": 0,
    "onlineUsers": 0,
    "totalArchives": 0,
    "totalCourses": 0,
    "activeToday": 0,
}


async def _get_cached() -> dict | None:
    try:
        cached = await get_redis().get(CACHE_KEY)
    except Exception:
        logger.warning("Failed to read statistics cache", exc_info=True)
        return None
    return json.loads(cached) if cached else None


async def _set_cached(data: dict) -> None:
    try:
        await get_redis().set(CACHE_KEY, json.dumps(data), ex=CACHE_TTL_SECONDS)
    except Exception:
        logger.warning("Failed to write statistics cache", exc_info=True)


async def _count_activity() -> tuple[int, int]:
    try:
        return await count_online_users(), await count_active_today()
    except Exception:
        logger.warning("Failed to read user activity", exc_info=True)
        return 0, 0


@router.get("/statistics")
async def get_system_statistics(db: AsyncSession = Depends(get_session)):
    """Get system-wide statistics"""
    cached = await _get_cached()
    if cached is not None:
        return {"success": True, "data": cached}

    try:
        total_users = (
            select(func.count(User.id)).where(User.deleted_at.is_(None)).scalar_subquery()
        )
        # Only courses that still have visible archives
        total_courses = (
            select(func.count(func.distinct(Archive.course_id)))
            .join(Course, Course.id == Archive.course_id)
            .where(Archive.deleted_at.is_(None), Course.deleted_at.is_(None))
            .scalar_subquery()
        )
        total_archives = (
            select(func.count(Archive.id))
            .where(Archive.deleted_at.is_(None))
            .scalar_subquery()
        )
        # Downloads of deleted archives still count, so the total never goes down
        total_downloads = select(
            func.coalesce(func.sum(Archive.download_count), 0)
        ).scalar_subquery()

        row = (
            await db.execute(
                select(total_users, total_courses, total_archives, total_downloads)
            )
        ).one()
    except Exception:
        logger.exception("Error fetching statistics")
        return {
            "success": False,
            "error": "Failed to fetch statistics.",
            "data": dict(EMPTY_STATISTICS),
        }

    online_users, active_today = await _count_activity()
    data = {
        "totalUsers": row[0],
        "totalDownloads": row[3],
        "onlineUsers": online_users,
        "totalArchives": row[2],
        "totalCourses": row[1],
        "activeToday": active_today,
    }
    await _set_cached(data)
    return {"success": True, "data": data}
