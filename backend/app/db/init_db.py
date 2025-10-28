import os
import subprocess
import unicodedata
from functools import lru_cache
from pathlib import Path

from sqlmodel import select, func, SQLModel
import yaml

from app.core.config import settings
from app.models.models import User, Meme, Course, CourseCategory
from app.utils.auth import get_password_hash
from app.db.session import engine, AsyncSessionLocal

SEED_DATA_PATH = Path(__file__).with_name("seed_data.yaml")


@lru_cache(maxsize=1)
def load_seed_data():
    with SEED_DATA_PATH.open(encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


async def init_db():
    # Run Alembic migrations instead of create_all
    try:
        # Run alembic upgrade head to apply all migrations
        result = subprocess.run(
            ["uv", "run", "alembic", "upgrade", "head"],
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Alembic migration failed: {result.stderr}")
            # Fallback to create_all if migration fails
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
                await conn.commit()
        else:
            print("Database migrations applied successfully")
    except Exception as e:
        print(f"Error running migrations: {e}")
        # Fallback to create_all
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            await conn.commit()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.name == settings.DEFAULT_ADMIN_NAME)
        )
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            admin_user = User(
                name=settings.DEFAULT_ADMIN_NAME,
                email=settings.DEFAULT_ADMIN_EMAIL,
                password_hash=get_password_hash(
                    settings.DEFAULT_ADMIN_PASSWORD
                ),
                is_local=True,
                is_admin=True
            )
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)

        result = await session.execute(
            select(func.count()).select_from(Course)
        )
        count = result.scalar()
        if count == 0:
            seed_data = load_seed_data()
            initial_courses = [
                Course(
                    name=unicodedata.normalize("NFKC", course["name"]),
                    category=CourseCategory[course["category"]],
                )
                for course in seed_data.get("courses", [])
            ]
            session.add_all(initial_courses)
            await session.commit()

        result = await session.execute(select(func.count()).select_from(Meme))
        count = result.scalar()
        if count == 0:
            seed_data = load_seed_data()
            initial_memes = [
                Meme(
                    content=meme["content"],
                    language=meme["language"],
                )
                for meme in seed_data.get("memes", [])
            ]
            session.add_all(initial_memes)
            await session.commit()


async def get_session():
    """
    Database dependency for FastAPI endpoints.
    """
    async with AsyncSessionLocal() as session:
        yield session
