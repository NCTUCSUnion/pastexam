import unicodedata

from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.models import Course, CourseCategory


def normalize_name(value: str) -> str:
    """Canonical form for course and professor names typed by users.

    NFKC folds full-width characters (e.g. "（一）" from Zhuyin input into "(一)"),
    and whitespace is trimmed and collapsed, so the same name typed twice matches.
    """
    return " ".join(unicodedata.normalize("NFKC", value).split())


def require_name(value: str, field: str) -> str:
    normalized = normalize_name(value)
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"{field} cannot be empty"
        )
    return normalized


async def find_course(
    db: AsyncSession,
    name: str,
    category: CourseCategory,
    *,
    exclude_id: int | None = None,
) -> Course | None:
    """Find a live course whose normalized name matches, so rows created before
    names were normalized are still found."""
    query = select(Course).where(
        Course.category == category, Course.deleted_at.is_(None)
    )
    if exclude_id is not None:
        query = query.where(Course.id != exclude_id)
    target = normalize_name(name)
    courses = (await db.execute(query.order_by(Course.id))).scalars().all()
    return next((c for c in courses if normalize_name(c.name) == target), None)
