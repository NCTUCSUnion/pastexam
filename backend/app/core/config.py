from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # PostgreSQL
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # OAuth
    OAUTH_CLIENT_ID: str
    OAUTH_CLIENT_SECRET: str
    OAUTH_AUTHORIZE_URL: str
    OAUTH_TOKEN_URL: str
    OAUTH_REDIRECT_URI: str
    OAUTH_USERINFO_URL: str
    FRONTEND_URL: str

    # MinIO
    MINIO_ENDPOINT: str
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_BUCKET_NAME: str
    EXTERNAL_ENDPOINT: str

    class Config:
        env_file = ".env"
        from_attributes = True

settings = Settings()

SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{settings.DB_USER}:{settings.DB_PASSWORD}@"
    f"{settings.DB_HOST}:{settings.DB_PORT}/"
    f"{settings.DB_NAME}"
) 