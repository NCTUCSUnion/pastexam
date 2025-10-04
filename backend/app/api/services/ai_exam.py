from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
import google.generativeai as genai
import io
import logging

from app.db.init_db import get_session
from app.models.models import User, Archive, Course, CourseCategory, ArchiveType
from app.utils.auth import get_current_user
from app.utils.storage import get_minio_client
from app.core.config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

router = APIRouter()

# TODO: 之後改成讓使用者自己設定 API key
GEMINI_API_KEY = "AIzaSyAG5psoGvUnfQVrwSCl-Q6oyGro7u1Bknk"  # 請替換成你的 Gemini API key

class GenerateExamRequest(BaseModel):
    archive_ids: List[int]
    prompt: Optional[str] = None
    temperature: Optional[float] = 0.7

class GenerateExamResponse(BaseModel):
    success: bool
    generated_content: str
    archives_used: List[dict]

@router.post("/generate", response_model=GenerateExamResponse)
async def generate_mock_exam(
    request: GenerateExamRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    基於指定的多份考古題生成模擬試題
    """
    logger.info(f"[AI生成] 開始處理請求 - archive_ids: {request.archive_ids}")
    
    if not request.archive_ids or len(request.archive_ids) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="至少需要選擇 1 份考古題"
        )
    
    # 查詢指定的考古題
    query = select(Archive, Course).join(Course).where(
        Archive.id.in_(request.archive_ids),
        Archive.deleted_at.is_(None),
        Course.deleted_at.is_(None)
    ).order_by(Archive.academic_year.desc())
    
    result = await db.execute(query)
    archives_with_courses = result.all()
    
    logger.info(f"[AI生成] 查詢到 {len(archives_with_courses)} 份考古題")
    
    if not archives_with_courses:
        logger.warning(f"[AI生成] 找不到指定的考古題")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到指定的考古題"
        )
    
    try:
        # 設定 Gemini API
        logger.info(f"[AI生成] 配置 Gemini API")
        genai.configure(api_key=GEMINI_API_KEY)
        minio_client = get_minio_client()
        
        # 上傳所有 PDF 到 Gemini
        uploaded_files = []
        archives_info = []
        
        logger.info(f"[AI生成] 開始上傳 {len(archives_with_courses)} 份 PDF 到 Gemini")
        for idx, (archive, course) in enumerate(archives_with_courses, 1):
            logger.info(f"[AI生成] [{idx}/{len(archives_with_courses)}] 從 MinIO 讀取: {archive.object_name}")
            # 從 MinIO 取得 PDF
            response = minio_client.get_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=archive.object_name
            )
            pdf_data = response.read()
            pdf_size = len(pdf_data)
            response.close()
            response.release_conn()
            logger.info(f"[AI生成] [{idx}/{len(archives_with_courses)}] PDF 大小: {pdf_size/1024:.2f} KB")
            
            # 上傳到 Gemini
            logger.info(f"[AI生成] [{idx}/{len(archives_with_courses)}] 上傳到 Gemini API")
            uploaded_file = genai.upload_file(io.BytesIO(pdf_data), mime_type="application/pdf")
            uploaded_files.append(uploaded_file)
            logger.info(f"[AI生成] [{idx}/{len(archives_with_courses)}] Gemini 檔案 URI: {uploaded_file.uri}")
            
            archives_info.append({
                "id": archive.id,
                "name": archive.name,
                "course": course.name,
                "professor": archive.professor,
                "academic_year": archive.academic_year,
                "archive_type": archive.archive_type
            })

        logger.info(f"[AI生成] 使用模型: gemini-2.5-flash")
        model = genai.GenerativeModel('gemini-2.5-flash')

        course_name = archives_info[0]["course"]
        professor = archives_info[0]["professor"]
        
        default_prompt = f"""
請基於這 {len(archives_info)} 份 {course_name} 的 {professor} 教授的考古題，生成一份全新的模擬試題。

考古題資訊：
{chr(10).join([f"- {info['academic_year']} 學年度 {info['name']} ({info['archive_type']})" for info in archives_info])}

請仔細分析這些考古題的：
1. 出題風格和格式
2. 題目類型和題數
3. 難度分布
4. 常見主題和重點
5. 不同年份或類型的考題之間的共同點和差異

然後生成一份新的模擬試題，要求：
1. 題目格式要和原考古題相似
2. 難度要相當
3. 涵蓋這些考古題中出現過的主題範圍
4. 如果原考古題有答案，也請提供答案
5. 要有創新性，不要只是重複原題
6. 融合不同考古題的風格，生成一份完整的試題

請用繁體中文回答，並清楚標示題號和分數。
"""
        
        prompt = request.prompt if request.prompt else default_prompt
        
        # 準備內容：所有 PDF + prompt
        content = uploaded_files + [prompt]
        logger.info(f"[AI生成] Prompt 長度: {len(prompt)} 字元")
        
        # 生成內容
        logger.info(f"[AI生成] 開始呼叫 Gemini API 生成內容 (temperature={request.temperature})")
        response = model.generate_content(
            content,
            generation_config=genai.types.GenerationConfig(
                temperature=request.temperature,
            )
        )
        
        logger.info(f"[AI生成] Gemini API 回應成功，內容長度: {len(response.text)} 字元")
        
        # 刪除所有上傳的檔案
        logger.info(f"[AI生成] 清理 Gemini 上傳的檔案")
        for uploaded_file in uploaded_files:
            genai.delete_file(uploaded_file.name)
        
        logger.info(f"[AI生成] 完成！使用了 {len(archives_info)} 份考古題生成模擬試題")
        return GenerateExamResponse(
            success=True,
            generated_content=response.text,
            archives_used=archives_info
        )
        
    except Exception as e:
        logger.error(f"[AI生成] 發生錯誤: {type(e).__name__}: {str(e)}", exc_info=True)
        # 確保刪除所有上傳的檔案
        for uploaded_file in uploaded_files:
            try:
                genai.delete_file(uploaded_file.name)
            except:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成失敗: {str(e)}"
        )

@router.get("/test")
async def test_ai_service():
    """測試 AI service 是否正常運作"""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Say hello in Traditional Chinese")
        return {
            "success": True,
            "message": "AI service is working",
            "test_response": response.text
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service test failed: {str(e)}"
        )

