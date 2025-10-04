import io
from typing import List, Optional
import google.generativeai as genai
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import settings
from app.db.init_db import engine
from app.models.models import Archive, Course
from app.utils.storage import get_minio_client

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

async def generate_exam_content(archive_ids: List[int], user_id: int, prompt: Optional[str] = None, temperature: float = 0.7) -> dict:
    """
    Core AI exam generation logic
    
    Args:
        archive_ids: List of archive IDs
        prompt: Custom prompt (optional)
        temperature: Generation temperature
        
    Returns:
        dict: Generation result with success status, content, and archives used
    """
    # logger.info(f"[AI Exam] Starting generation for archive_ids: {archive_ids}, user_id: {user_id}")
    
    async with AsyncSession(engine) as db:
        # Get user's API key
        from app.models.models import User
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user or not user.gemini_api_key:
            raise ValueError("User API key not found. Please configure your Gemini API key first.")
        
        api_key = user.gemini_api_key
        query = select(Archive, Course).join(Course).where(
            Archive.id.in_(archive_ids),
            Archive.deleted_at.is_(None),
            Course.deleted_at.is_(None)
        ).order_by(Archive.academic_year.desc())
        
        result = await db.execute(query)
        archives_with_courses = result.all()
        
        if not archives_with_courses:
            raise ValueError("Archives not found")
        
        genai.configure(api_key=api_key)
        minio_client = get_minio_client()
        
        uploaded_files = []
        archives_info = []
        
        try:
            # logger.info(f"[AI Exam] Uploading {len(archives_with_courses)} PDFs to Gemini")
            for idx, (archive, course) in enumerate(archives_with_courses, 1):
                response = minio_client.get_object(
                    bucket_name=settings.MINIO_BUCKET_NAME,
                    object_name=archive.object_name
                )
                pdf_data = response.read()
                response.close()
                response.release_conn()
                
                uploaded_file = genai.upload_file(io.BytesIO(pdf_data), mime_type="application/pdf")
                uploaded_files.append(uploaded_file)
                
                archives_info.append({
                    "id": archive.id,
                    "name": archive.name,
                    "course": course.name,
                    "professor": archive.professor,
                    "academic_year": archive.academic_year,
                    "archive_type": archive.archive_type
                })

            model = genai.GenerativeModel('gemini-2.5-flash')

            course_name = archives_info[0]["course"]
            professor = archives_info[0]["professor"]
            
            default_prompt = f"""You are a teaching assistant for Professor {professor}'s {course_name} course. Your task is to generate a NEW exam based on {len(archives_info)} past exam papers provided.

Past Exam Information:
{chr(10).join([f"- {info['academic_year']} {info['name']} ({info['archive_type']})" for info in archives_info])}

CRITICAL REQUIREMENTS:
1. OUTPUT ONLY THE EXAM QUESTIONS - Do NOT include any analysis, explanation, or thought process
2. MIMIC THE PROFESSOR'S STYLE EXACTLY:
   - Use the SAME LANGUAGE the professor uses (if exams are in Chinese, generate in Chinese; if in English, generate in English; if mixed, use the same mix)
   - Follow the SAME QUESTION FORMAT and structure
   - Use the SAME QUESTION TYPES (multiple choice, short answer, essay, calculations, etc.)
   - Match the SAME DIFFICULTY LEVEL
   - Follow the SAME POINT DISTRIBUTION
   - Use similar terminology and phrasing style

3. EXAM STRUCTURE:
   - Generate questions covering similar topics from the provided exams
   - Maintain the same number of questions or similar exam length
   - Number questions clearly and indicate point values

4. ANSWER KEY - MANDATORY:
   - ALWAYS provide a reference answer key at the end of the exam
   - Provide detailed solutions for calculation/problem-solving questions
   - Include explanations for conceptual questions
   - Use the same language as the questions

5. QUALITY STANDARDS:
   - Questions must be ORIGINAL - do not copy directly from provided exams
   - Questions should test the same concepts but with different scenarios/numbers/examples
   - Maintain academic rigor and proper grammar

6. STRICT OUTPUT FORMAT:
   - Start with exam questions immediately
   - Add a clear separator (e.g., "===== 參考解答 =====" or "===== ANSWER KEY =====")
   - End with the complete answer key
   - DO NOT add any concluding statements like "預期的結果", "expected results", "總結", "summary", or similar phrases
   - DO NOT add any meta-commentary about the exam generation process
   - END IMMEDIATELY after the answer key

START YOUR RESPONSE IMMEDIATELY WITH THE EXAM CONTENT. DO NOT include phrases like "Here is the exam" or "Based on my analysis". Just output the exam and stop after the answer key.
"""
            
            final_prompt = prompt if prompt else default_prompt
            content = uploaded_files + [final_prompt]
            
            # logger.info(f"[AI Exam] Calling Gemini API (temperature={temperature})")
            response = model.generate_content(
                content,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                )
            )
            
            # logger.info(f"[AI Exam] Generation completed successfully")
            
            for uploaded_file in uploaded_files:
                genai.delete_file(uploaded_file.name)
            
            disclaimer = """⚠️ 注意事項 / NOTICE ⚠️
此試題由 AI 自動生成，僅供參考練習使用。
答案可能有誤，請務必自行確認正確性。
This exam is AI-generated for reference and practice only.
Answers may contain errors. Please verify the correctness yourself.

================================================================================

"""
            
            return {
                "success": True,
                "generated_content": disclaimer + response.text,
                "archives_used": archives_info
            }
            
        except Exception as e:
            # logger.error(f"[AI Exam] Error: {type(e).__name__}: {str(e)}")
            for uploaded_file in uploaded_files:
                try:
                    genai.delete_file(uploaded_file.name)
                except:
                    pass
            raise


async def generate_ai_exam_task(ctx, task_data: dict):
    """
    ARQ worker task for AI exam generation
    
    Args:
        ctx: ARQ context
        task_data: Task data containing archive_ids, user_id, prompt, temperature
    """
    # logger.info(f"[Worker] Processing task for user {task_data.get('user_id')}")
    
    try:
        result = await generate_exam_content(
            archive_ids=task_data['archive_ids'],
            user_id=task_data['user_id'],
            prompt=task_data.get('prompt'),
            temperature=task_data.get('temperature', 0.7)
        )
        
        # logger.info(f"[Worker] Task completed successfully")
        return result
        
    except Exception as e:
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
