from fastapi import APIRouter, Depends, HTTPException, status
import logging
import json
from datetime import datetime

from app.models.models import (
    User,
    GenerateExamRequest,
    TaskSubmitResponse,
    TaskStatusResponse,
    GenerateExamResponse
)
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

router = APIRouter()


@router.post("/generate", response_model=TaskSubmitResponse)
async def submit_generate_task(
    request: GenerateExamRequest,
    current_user: User = Depends(get_current_user),
):
    """Submit AI exam generation task"""
    from app.worker import get_redis_pool
    
    logger.info(f"[API] Task submitted by user {current_user.user_id} with {len(request.archive_ids)} archives")
    
    if not request.archive_ids or len(request.archive_ids) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="至少需要選擇 1 份考古題"
        )
    
    try:
        redis = await get_redis_pool()
        
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
        
        logger.info(f"[API] Task enqueued: {job.job_id}")
        
        return TaskSubmitResponse(
            task_id=job.job_id,
            status="pending",
            message="任務已提交，請稍後查詢結果"
        )
        
    except Exception as e:
        logger.error(f"[API] Failed to submit task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交任務失敗: {str(e)}"
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
                detail="找不到該任務"
            )
        
        metadata = json.loads(metadata_str.decode("utf-8"))
        
        if metadata["user_id"] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="無權訪問此任務"
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
                logger.warning(f"[API] Job complete but result fetch failed: {e}")
            response.result = result
            response.completed_at = metadata.get("completed_at") or datetime.utcnow().isoformat()
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Failed to get task status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢任務狀態失敗: {str(e)}"
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
        logger.error(f"[API] Failed to list tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出任務失敗: {str(e)}"
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
                detail="找不到該任務"
            )
        
        metadata = json.loads(metadata_str)
        
        if metadata["user_id"] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="無權刪除此任務"
            )
        
        await redis.delete(metadata_key)
        await redis.delete(f"arq:result:{task_id}")
        
        return {"success": True, "message": "任務已刪除"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Failed to delete task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除任務失敗: {str(e)}"
        )


