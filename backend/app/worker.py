import asyncio
import io
import logging
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import ClassVar
from weakref import WeakKeyDictionary

from arq import ArqRedis, create_pool
from arq.connections import RedisSettings
from google import genai
from google.genai.types import UploadFileConfig
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.db.init_db import engine
from app.models.models import Archive, Course
from app.utils.crypto import decrypt_secret
from app.utils.storage import get_storage_client

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)


PROMPT_TEMPLATE_PATH = (
    Path(__file__).resolve().parent / "templates" / "ai_exam_prompt.txt"
)


def _read_object(storage_client, object_name: str) -> bytes:
    response = storage_client.get_object(
        bucket_name=settings.RUSTFS_BUCKET_NAME,
        object_name=object_name,
    )
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


@lru_cache(maxsize=1)
def load_default_prompt_template() -> str:
    return PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")


async def generate_exam_content(
    archive_ids: list[int],
    user_id: int,
    prompt: str | None = None,
    temperature: float | None = None,
) -> dict:
    """
    Core AI exam generation logic

    Args:
        archive_ids: List of archive IDs
        prompt: Custom prompt (optional)
        temperature: Generation temperature

    Returns:
        dict: Generation result with success status, content, and archives used
    """
    # logger.info(
    #     f"[AI Exam] Starting generation for archive_ids: {archive_ids}, "
    #     f"user_id: {user_id}"
    # )

    async with AsyncSession(engine) as db:
        # Get user's API key
        from app.models.models import User

        user_query = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        api_key = decrypt_secret(user.gemini_api_key) if user else None
        if not api_key:
            raise ValueError(
                "User API key not found. Please configure your Gemini API key first."
            )

        query = (
            select(Archive, Course)
            .join(Course)
            .where(
                Archive.id.in_(archive_ids),
                Archive.deleted_at.is_(None),
                Course.deleted_at.is_(None),
            )
            .order_by(Archive.academic_year.desc())
        )

        result = await db.execute(query)
        archives_with_courses = result.all()

        if not archives_with_courses:
            raise ValueError("Archives not found")

        client = genai.Client(api_key=api_key)
        storage_client = await asyncio.to_thread(get_storage_client)

        uploaded_files = []
        archives_info = []

        try:
            # logger.info(
            #     "[AI Exam] Uploading %s PDFs to Gemini",
            #     len(archives_with_courses),
            # )
            for idx, (archive, course) in enumerate(archives_with_courses, 1):
                # Storage and Gemini SDK calls are blocking; keep them off the event loop
                pdf_data = await asyncio.to_thread(
                    _read_object, storage_client, archive.object_name
                )

                upload_config = UploadFileConfig(mime_type="application/pdf")
                uploaded_file = await asyncio.to_thread(
                    client.files.upload, file=io.BytesIO(pdf_data), config=upload_config
                )
                uploaded_files.append(uploaded_file)

                archives_info.append(
                    {
                        "id": archive.id,
                        "name": archive.name,
                        "course": course.name,
                        "professor": archive.professor,
                        "academic_year": archive.academic_year,
                        "archive_type": archive.archive_type,
                    }
                )

            course_name = archives_info[0]["course"]
            professor = archives_info[0]["professor"]

            archives_details = "\n".join(
                [
                    "- {academic_year} {name} ({archive_type})".format(**info)
                    for info in archives_info
                ]
            )

            default_prompt = load_default_prompt_template().format(
                professor=professor,
                course_name=course_name,
                archives_count=len(archives_info),
                archives_details=archives_details,
            )

            final_prompt = prompt if prompt else default_prompt
            content = uploaded_files + [final_prompt]

            # logger.info(
            #     "[AI Exam] Calling Gemini API (temperature=%s)",
            #     temperature,
            # )
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=settings.GEMINI_MODEL,
                contents=content,
                config={"temperature": temperature} if temperature is not None else None,
            )

            # logger.info(f"[AI Exam] Generation completed successfully")

            for uploaded_file in uploaded_files:
                await asyncio.to_thread(client.files.delete, name=uploaded_file.name)

            disclaimer = """⚠️ 注意事項 / NOTICE ⚠️
此試題由 AI 自動生成，僅供參考練習使用。
答案可能有誤，請務必自行確認正確性。
This exam is AI-generated for reference and practice only.
Answers may contain errors. Please verify the correctness yourself.

{separator}

"""

            generated_content = disclaimer.format(separator="=" * 80) + response.text

            return {
                "success": True,
                "generated_content": generated_content,
                "archives_used": archives_info,
            }

        except Exception:
            # logger.error(f"[AI Exam] Error: {type(e).__name__}: {str(e)}")
            for uploaded_file in uploaded_files:
                try:
                    await asyncio.to_thread(client.files.delete, name=uploaded_file.name)
                except Exception:
                    logger.warning(
                        "Failed to delete uploaded Gemini file during cleanup: %s",
                        uploaded_file.name,
                        exc_info=True,
                    )
            raise


async def generate_ai_exam_task(ctx, task_data: dict):
    """
    ARQ worker task to generate exams with AI.

    Args:
        ctx: ARQ context
        task_data: requires archive_ids, user_id, prompt, temperature
    """
    # logger.info(
    #     "[Worker] Processing task for user %s",
    #     task_data.get("user_id"),
    # )

    redis = None
    task_id = None
    if ctx is None:
        redis = None
        task_id = None
    else:
        if not isinstance(ctx, dict):
            raise TypeError("ARQ ctx must be a dict")
        if "redis" not in ctx or "job_id" not in ctx:
            raise KeyError("ARQ ctx missing required keys: redis/job_id")
        redis = ctx.get("redis")
        task_id = ctx.get("job_id")
        if isinstance(task_id, bytes):
            task_id = task_id.decode("utf-8", errors="ignore")

    async def publish_event(status: str, *, error: str | None = None):
        if not redis or not task_id:
            return
        try:
            fields = {"status": status, "ts": datetime.now(UTC).isoformat()}
            if error:
                fields["error"] = error
            stream_key = f"ai_exam:task_events:{task_id}"
            await redis.xadd(stream_key, fields)
            await redis.expire(stream_key, 86400)
        except Exception:
            # Event streaming is best-effort; do not fail the job if Redis Streams is unavailable.
            logger.exception("Failed to publish ai_exam event (task_id=%s)", task_id)

    try:
        await publish_event("in_progress")
        result = await generate_exam_content(
            archive_ids=task_data["archive_ids"],
            user_id=task_data["user_id"],
            prompt=task_data.get("prompt"),
            temperature=task_data.get("temperature"),
        )

        # logger.info(f"[Worker] Task completed successfully")
        await publish_event("complete")
        return result

    except Exception as e:
        await publish_event("failed", error=str(e))
        # logger.error(f"[Worker] Task failed: {str(e)}")
        raise


class WorkerSettings:
    """ARQ worker settings"""

    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    functions: ClassVar[list] = [generate_ai_exam_task]

    max_jobs = 5  # Max concurrent jobs
    job_timeout = 600  # Job timeout in seconds
    keep_result = 86400  # Keep results for 24 hours


_redis_pools: WeakKeyDictionary[asyncio.AbstractEventLoop, ArqRedis] = (
    WeakKeyDictionary()
)


async def get_redis_pool() -> ArqRedis:
    """Get the ARQ Redis pool for the running event loop, creating it once"""
    loop = asyncio.get_running_loop()
    pool = _redis_pools.get(loop)
    if pool is None:
        pool = await create_pool(WorkerSettings.redis_settings)
        _redis_pools[loop] = pool
    return pool
