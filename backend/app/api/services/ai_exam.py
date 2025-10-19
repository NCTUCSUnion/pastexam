from fastapi import APIRouter, Depends, HTTPException, status
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from arq.jobs import Job, JobStatus

from app.models.models import (
    User,
    GenerateExamRequest,
    TaskSubmitResponse,
    TaskStatusResponse,
    GenerateExamResponse,
    ApiKeyUpdate,
    ApiKeyResponse
)
from app.utils.auth import get_current_user
from app.db.session import get_session

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

# if not logger.handlers:
#     console_handler = logging.StreamHandler()
#     console_handler.setLevel(logging.INFO)
#     formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
#     console_handler.setFormatter(formatter)
#     logger.addHandler(console_handler)

router = APIRouter()


@router.post("/generate", response_model=TaskSubmitResponse)
async def submit_generate_task(
    request: GenerateExamRequest,
    current_user: User = Depends(get_current_user),
):
    """Submit AI exam generation task"""
    from app.worker import get_redis_pool
    
    # logger.info(f"[API] Task submitted by user {current_user.user_id} with {len(request.archive_ids)} archives")
    
    if not request.archive_ids or len(request.archive_ids) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 1 archive is required"
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
                
                if job_status_enum in [JobStatus.queued, JobStatus.deferred, JobStatus.in_progress]:
                    active_jobs.append(task_id)
        
        if active_jobs:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have an active task. Please wait for it to complete before submitting a new one."
            )
        
        task_data = {
            "archive_ids": request.archive_ids,
            "user_id": current_user.user_id,
            "prompt": request.prompt,
            "temperature": request.temperature
        }
        
        job = await redis.enqueue_job(
            'generate_ai_exam_task',
            task_data
        )
        
        metadata = {
            "user_id": current_user.user_id,
            "archive_ids": request.archive_ids,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }
        await redis.set(
            f"task_metadata:{job.job_id}",
            json.dumps(metadata),
            ex=86400  # 24 hours TTL
        )
        
        # logger.info(f"[API] Task enqueued: {job.job_id}")
        
        return TaskSubmitResponse(
            task_id=job.job_id,
            status="pending",
            message="Task submitted, please check results later"
        )
        
    except Exception as e:
        # logger.error(f"[API] Failed to submit task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit task: {str(e)}"
        )


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get task status"""
    from app.worker import get_redis_pool
    from arq.jobs import Job, JobStatus
    
    try:
        redis = await get_redis_pool()
        
        metadata_key = f"task_metadata:{task_id}"
        metadata_str = await redis.get(metadata_key)
        
        if not metadata_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        metadata = json.loads(metadata_str.decode("utf-8"))
        
        if metadata["user_id"] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this task"
            )
        
        job = Job(task_id, redis)

        job_status_enum = await job.status()
        if job_status_enum is None:
            job_status = "not_found"
        else:
            status_map = {
                JobStatus.queued: "pending",
                JobStatus.deferred: "pending",
                JobStatus.in_progress: "in_progress",
                JobStatus.complete: "complete",
                JobStatus.not_found: "not_found",
            }
            job_status = status_map.get(job_status_enum, "unknown")
        
        response = TaskStatusResponse(
            task_id=task_id,
            status=job_status,
            created_at=metadata.get("created_at")
        )
        
        if job_status == "complete":
            try:
                result = await job.result()
            except Exception as e:
                result = None
                # logger.warning(f"[API] Job complete but result fetch failed: {e}")
            response.result = result
            response.completed_at = metadata.get("completed_at") or datetime.utcnow().isoformat()
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        # logger.error(f"[API] Failed to get task status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/tasks")
async def list_user_tasks(
    current_user: User = Depends(get_current_user),
):
    """List all tasks for the current user"""
    from app.worker import get_redis_pool
    from arq.jobs import Job, JobStatus
    
    try:
        redis = await get_redis_pool()
        
        tasks = []
        async for key in redis.scan_iter(match="task_metadata:*"):
            metadata_str = await redis.get(key)
            if not metadata_str:
                continue

            metadata = json.loads(metadata_str.decode("utf-8"))
            if metadata.get("user_id") != current_user.user_id:
                continue

            task_id = key.decode().replace("task_metadata:", "")
            job = Job(task_id, redis)

            job_status_enum = await job.status()
            if job_status_enum is None:
                job_status = "not_found"
            else:
                status_map = {
                    JobStatus.queued: "pending",
                    JobStatus.deferred: "pending",
                    JobStatus.in_progress: "in_progress",
                    JobStatus.complete: "complete",
                    JobStatus.not_found: "not_found",
                }
                job_status = status_map.get(job_status_enum, "unknown")

            tasks.append({
                "task_id": task_id,
                "status": job_status,
                "created_at": metadata.get("created_at"),
                "archive_ids": metadata.get("archive_ids", []),
            })
        
        tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return {"tasks": tasks}
        
    except Exception as e:
        # logger.error(f"[API] Failed to list tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tasks: {str(e)}"
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        metadata = json.loads(metadata_str)
        
        if metadata["user_id"] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to delete this task"
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
            detail=f"Failed to delete task: {str(e)}"
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
        user_query = select(User).where(User.id == current_user.user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            return ApiKeyResponse(has_api_key=False, api_key_masked=None)
        
        has_api_key = bool(user.gemini_api_key)
        api_key_masked = None
        
        if has_api_key:
            # Show only last 4 characters
            api_key_masked = f"****{user.gemini_api_key[-4:]}"
        
        return ApiKeyResponse(
            has_api_key=has_api_key,
            api_key_masked=api_key_masked
        )
    except Exception as e:
        # logger.error(f"[API] Failed to get API key status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API key status: {str(e)}"
        )


@router.put("/api-key", response_model=ApiKeyResponse)
async def update_api_key(
    request: ApiKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Update user's API key"""
    from sqlmodel import update, select
    
    try:
        if request.gemini_api_key:
            from google import genai
            
            client = genai.Client(api_key=request.gemini_api_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents="Hello"
            )
        
        stmt = update(User).where(User.id == current_user.user_id).values(
            gemini_api_key=request.gemini_api_key
        )
        await db.execute(stmt)
        await db.commit()
        
        # Get updated user data
        user_query = select(User).where(User.id == current_user.user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        has_api_key = bool(user.gemini_api_key) if user else False
        api_key_masked = None
        
        if has_api_key and user:
            api_key_masked = f"****{user.gemini_api_key[-4:]}"
        
        return ApiKeyResponse(
            has_api_key=has_api_key,
            api_key_masked=api_key_masked
        )
    except Exception as e:
        # logger.error(f"[API] Failed to update API key: {str(e)}")
        
        # Check if it's an API key validation error
        if "API key" in str(e) or "authentication" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid API Key: {str(e)}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update API key: {str(e)}"
            )


