from fastapi import APIRouter

from app.api.services import auth, courses, archives, meme, users, statistics, ai_exam

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(archives.router, prefix="/archives", tags=["archives"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(meme.router, tags=["meme"])
api_router.include_router(statistics.router, tags=["statistics"])
api_router.include_router(ai_exam.router, prefix="/ai-exam", tags=["ai-exam"]) 