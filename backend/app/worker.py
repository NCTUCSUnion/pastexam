import io
import logging
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from arq import create_pool
from arq.connections import RedisSettings
from google import genai
from google.genai.types import UploadFileConfig
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.db.init_db import engine
from app.models.models import Archive, Course
from app.utils.storage import get_minio_client

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)


PROMPT_TEMPLATE_PATH = (
    Path(__file__).resolve().parent / "templates" / "ai_exam_prompt.txt"
)


@lru_cache(maxsize=1)
def load_default_prompt_template() -> str:
    return PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")


async def generate_exam_content(
    archive_ids: List[int],
    user_id: int,
    prompt: Optional[str] = None,
    temperature: float = 0.7,
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

        if not user or not user.gemini_api_key:
            raise ValueError(
                ("User API key not found. Please configure your Gemini API key first.")
            )

        api_key = user.gemini_api_key
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
        minio_client = get_minio_client()

        uploaded_files = []
        archives_info = []

        try:
            # logger.info(
            #     "[AI Exam] Uploading %s PDFs to Gemini",
            #     len(archives_with_courses),
            # )
            for idx, (archive, course) in enumerate(archives_with_courses, 1):
                response = minio_client.get_object(
                    bucket_name=settings.MINIO_BUCKET_NAME,
                    object_name=archive.object_name,
                )
                pdf_data = response.read()
                response.close()
                response.release_conn()

                upload_config = UploadFileConfig(mime_type="application/pdf")
                uploaded_file = client.files.upload(
                    file=io.BytesIO(pdf_data), config=upload_config
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
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=content,
                config={"temperature": temperature},
            )

            # logger.info(f"[AI Exam] Generation completed successfully")

            for uploaded_file in uploaded_files:
                client.files.delete(name=uploaded_file.name)

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
                    client.files.delete(name=uploaded_file.name)
                except Exception:
                    pass
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
            fields = {"status": status, "ts": datetime.utcnow().isoformat()}
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
            temperature=task_data.get("temperature", 0.7),
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
    functions = [generate_ai_exam_task]

    max_jobs = 5  # Max concurrent jobs
    job_timeout = 600  # Job timeout in seconds
    keep_result = 86400  # Keep results for 24 hours


async def get_redis_pool():
    """Get Redis connection pool"""
    return await create_pool(WorkerSettings.redis_settings)
