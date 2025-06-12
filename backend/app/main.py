import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.api.api import api_router
from app.db.init_db import init_db

app = FastAPI(title="Past Exam API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[settings.FRONTEND_URL],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=3600
)

app.include_router(api_router)

@app.on_event("startup")
async def on_startup():
    await init_db()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 