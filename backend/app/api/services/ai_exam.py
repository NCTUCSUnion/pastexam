import asyncio
import json
from datetime import datetime, timezone

from arq.jobs import Job, JobStatus
from fastapi import APIRouter, Depends, HTTPException, WebSocket, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.models import (
    ApiKeyResponse,
    ApiKeyUpdate,
    GenerateExamRequest,
    TaskStatusResponse,
    TaskSubmitResponse,
    User,
)
from app.utils.auth import get_current_user
from app.utils.auth_ws import get_ws_token_payload

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

# if not logger.handlers:
#     console_handler = logging.StreamHandler()
#     console_handler.setLevel(logging.INFO)
#     formatter = logging.Formatter(
#         '%(asctime)s - %(levelname)s - %(message)s',
#         datefmt='%Y-%m-%d %H:%M:%S'
#     )
#     console_handler.setFormatter(formatter)
#     logger.addHandler(console_handler)

router = APIRouter()

_STATUS_MAP = {
    JobStatus.queued: "pending",
    JobStatus.deferred: "pending",
    JobStatus.in_progress: "in_progress",
    JobStatus.complete: "complete",
    JobStatus.not_found: "not_found",
}

TASK_EVENT_STREAM_BLOCK_MS = 5000


@router.websocket("/ws/task/{task_id}")
async def stream_task_status(
    websocket: WebSocket, task_id: str, db: AsyncSession = Depends(get_session)
):
    await websocket.accept()

    payload = await get_ws_token_payload(websocket)
    if not payload:
        await websocket.close(code=4401)
        return
    user_id = payload.get("uid")
    if not user_id:
        await websocket.close(code=4401)
        return
    exp = payload.get("exp")
    exp_ts = float(exp) if exp is not None else None

    from app.worker import get_redis_pool

    try:
        redis = await get_redis_pool()

        metadata_key = f"task_metadata:{task_id}"
        metadata_str = await redis.get(metadata_key)
        if not metadata_str:
            await websocket.close(code=1008)
            return

        metadata = json.loads(metadata_str.decode("utf-8"))
        if metadata.get("user_id") != user_id:
            await websocket.close(code=1008)
            return

        stream_key = f"ai_exam:task_events:{task_id}"

        job = Job(task_id, redis)
        job_status_enum = await job.status()
        if job_status_enum is None:
            job_status = "not_found"
        else:
            job_status = _STATUS_MAP.get(job_status_enum, "unknown")

        response = TaskStatusResponse(
            task_id=task_id,
            status=job_status,
            created_at=metadata.get("created_at"),
        )

        def _extract_status(fields):
            if not isinstance(fields, dict):
                return ""
            status_raw = fields.get(b"status") or fields.get("status")
            if isinstance(status_raw, bytes):
                return status_raw.decode("utf-8", errors="ignore").strip()
            return str(status_raw or "").strip()

        def _extract_error(fields):
            if not isinstance(fields, dict):
                return None
            error_raw = fields.get(b"error") or fields.get("error")
            if isinstance(error_raw, bytes):
                return error_raw.decode("utf-8", errors="ignore")
            if error_raw is None:
                return None
            return str(error_raw)

        async def _get_job_result():
            last_err: Exception | None = None
            for _ in range(5):
                try:
                    res = await job.result()
                    if res is None:
                        pass
                    elif isinstance(res, dict):
                        return res
                    else:
                        raise TypeError("Task result must be a dict")
                except Exception as e:
                    last_err = e
                await asyncio.sleep(0.05)
            if last_err:
                raise last_err
            return None

        if job_status == "complete":
            response.result = await _get_job_result()
            response.completed_at = (
                metadata.get("completed_at") or datetime.utcnow().isoformat()
            )
            await websocket.send_json(response.dict())
            await websocket.close(code=1000)
            return

        await websocket.send_json(response.dict())

        if job_status in {"not_found"}:
            await websocket.close(code=1000)
            return

        last_stream_id = "0-0"
        last_sent_status = job_status

        while True:
            if exp_ts is not None and exp_ts < datetime.now(timezone.utc).timestamp():
                await websocket.close(code=4401)
                return

            streams = await redis.xread(
                {stream_key: last_stream_id},
                count=10,
                block=TASK_EVENT_STREAM_BLOCK_MS,
            )
            if not streams:
                # Fallback: if stream events were not published for any reason,
                # still keep the client updated by checking ARQ job status.
                try:
                    status_enum = await job.status()
                    current_status = (
                        "not_found"
                        if status_enum is None
                        else _STATUS_MAP.get(status_enum, "unknown")
                    )
                except Exception:
                    current_status = last_sent_status

                if current_status and current_status != last_sent_status:
                    last_sent_status = current_status

                    if current_status == "complete":
                        result = await _get_job_result()
                        completed_at = datetime.utcnow().isoformat()
                        metadata["completed_at"] = completed_at
                        metadata["status"] = "complete"
                        await redis.set(
                            metadata_key,
                            json.dumps(metadata),
                            ex=86400,
                        )

                        await websocket.send_json(
                            TaskStatusResponse(
                                task_id=task_id,
                                status="complete",
                                created_at=metadata.get("created_at"),
                                completed_at=completed_at,
                                result=result,
                            ).dict()
                        )
                        await websocket.close(code=1000)
                        return

                    await websocket.send_json(
                        TaskStatusResponse(
                            task_id=task_id,
                            status=current_status,
                            created_at=metadata.get("created_at"),
                        ).dict()
                    )

                continue

            for _stream_name, entries in streams:
                for entry_id, fields in entries:
                    last_stream_id = entry_id

                    status_value = _extract_status(fields)

                    if not status_value or status_value == last_sent_status:
                        continue
                    last_sent_status = status_value

                    if status_value == "failed":
                        error_value = _extract_error(fields)

                        await websocket.send_json(
                            TaskStatusResponse(
                                task_id=task_id,
                                status="failed",
                                created_at=metadata.get("created_at"),
                                error=error_value,
                            ).dict()
                        )
                        await websocket.close(code=1011)
                        return

                    if status_value != "complete":
                        await websocket.send_json(
                            TaskStatusResponse(
                                task_id=task_id,
                                status=status_value,
                                created_at=metadata.get("created_at"),
                            ).dict()
                        )
                        continue

                    result = await _get_job_result()

                    completed_at = datetime.utcnow().isoformat()
                    metadata["completed_at"] = completed_at
                    metadata["status"] = "complete"
                    await redis.set(
                        metadata_key,
                        json.dumps(metadata),
                        ex=86400,
                    )

                    await websocket.send_json(
                        TaskStatusResponse(
                            task_id=task_id,
                            status="complete",
                            created_at=metadata.get("created_at"),
                            completed_at=completed_at,
                            result=result,
                        ).dict()
                    )
                    await websocket.close(code=1000)
                    return
    except Exception:
        await websocket.close(code=1011)
        return


@router.post("/generate", response_model=TaskSubmitResponse)
async def submit_generate_task(
    request: GenerateExamRequest,
    current_user: User = Depends(get_current_user),
):
    """Submit AI exam generation task"""
    from app.worker import get_redis_pool

    # logger.info(
    #     f"[API] Task submitted by user {current_user.user_id} "
    #     f"with {len(request.archive_ids)} archives"
    # )
    if not request.archive_ids or len(request.archive_ids) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 1 archive is required",
        )

    try:
        redis = await get_redis_pool()

        # Check if user already has an active job
        active_jobs = []
        async for key in redis.scan_iter(match="task_metadata:*"):
            metadata_str = await redis.get(key)
            if not metadata_str:
                continue

            metadata = json.loads(metadata_str.decode("utf-8"))
            if metadata.get("user_id") == current_user.user_id:
                task_id = key.decode().replace("task_metadata:", "")
                job = Job(task_id, redis)
                job_status_enum = await job.status()

                if job_status_enum in [
                    JobStatus.queued,
                    JobStatus.deferred,
                    JobStatus.in_progress,
                ]:
                    active_jobs.append(task_id)

        if active_jobs:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "You already have an active task. Please wait for it to "
                    "complete before submitting a new one."
                ),
            )

        task_data = {
            "archive_ids": request.archive_ids,
            "user_id": current_user.user_id,
            "prompt": request.prompt,
            "temperature": request.temperature,
        }

        job = await redis.enqueue_job("generate_ai_exam_task", task_data)

        metadata = {
            "user_id": current_user.user_id,
            "archive_ids": request.archive_ids,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending",
        }
        await redis.set(
            f"task_metadata:{job.job_id}",
            json.dumps(metadata),
            ex=86400,  # 24 hours TTL
        )

        # logger.info(f"[API] Task enqueued: {job.job_id}")

        return TaskSubmitResponse(
            task_id=job.job_id,
            status="pending",
            message="Task submitted, please check results later",
        )

    except HTTPException:
        raise
    except Exception as e:
        # logger.error(f"[API] Failed to submit task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit task: {str(e)}",
        )


@router.delete("/task/{task_id}")
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a task"""
    from app.worker import get_redis_pool

    try:
        redis = await get_redis_pool()

        metadata_key = f"task_metadata:{task_id}"
        metadata_str = await redis.get(metadata_key)

        if not metadata_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        metadata = json.loads(metadata_str.decode("utf-8"))

        if metadata["user_id"] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to delete this task",
            )

        await redis.delete(metadata_key)
        await redis.delete(f"arq:result:{task_id}")

        return {"success": True, "message": "Task deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        # logger.error(f"[API] Failed to delete task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}",
        )


@router.get("/api-key", response_model=ApiKeyResponse)
async def get_api_key_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get user's API key status"""
    from sqlmodel import select

    try:
        # Get full user data from database
        user_query = select(User).where(
            User.id == current_user.user_id, User.deleted_at.is_(None)
        )
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            return ApiKeyResponse(has_api_key=False, api_key_masked=None)

        has_api_key = bool(user.gemini_api_key)
        api_key_masked = None

        if has_api_key:
            # Show only last 4 characters
            api_key_masked = f"****{user.gemini_api_key[-4:]}"

        return ApiKeyResponse(has_api_key=has_api_key, api_key_masked=api_key_masked)
    except HTTPException:
        raise
    except Exception as e:
        # logger.error(f"[API] Failed to get API key status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API key status: {str(e)}",
        )


@router.put("/api-key", response_model=ApiKeyResponse)
async def update_api_key(
    request: ApiKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Update user's API key"""
    from sqlmodel import select, update

    try:
        if request.gemini_api_key:
            from google import genai

            client = genai.Client(api_key=request.gemini_api_key)
            client.models.generate_content(model="gemini-2.5-flash", contents="Hello")

        stmt = (
            update(User)
            .where(User.id == current_user.user_id, User.deleted_at.is_(None))
            .values(gemini_api_key=request.gemini_api_key)
        )
        await db.execute(stmt)
        await db.commit()

        # Get updated user data
        user_query = select(User).where(
            User.id == current_user.user_id, User.deleted_at.is_(None)
        )
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        has_api_key = bool(user.gemini_api_key) if user else False
        api_key_masked = None

        if has_api_key and user:
            api_key_masked = f"****{user.gemini_api_key[-4:]}"

        return ApiKeyResponse(has_api_key=has_api_key, api_key_masked=api_key_masked)
    except HTTPException:
        raise
    except Exception as e:
        # logger.error(f"[API] Failed to update API key: {str(e)}")

        # Check if it's an API key validation error
        if "API key" in str(e) or "authentication" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid API Key: {str(e)}",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update API key: {str(e)}",
            )
