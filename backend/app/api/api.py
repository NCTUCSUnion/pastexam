from fastapi import APIRouter

from app.api.services import auth, courses, archives, meme, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(archives.router, prefix="/archives", tags=["archives"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(meme.router, tags=["meme"]) 