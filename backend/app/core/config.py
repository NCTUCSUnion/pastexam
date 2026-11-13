import logging

from pydantic import field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    OAUTH_CLIENT_ID: str
    OAUTH_CLIENT_SECRET: str
    OAUTH_AUTHORIZE_URL: str
    OAUTH_TOKEN_URL: str
    OAUTH_REDIRECT_URI: str
    OAUTH_USERINFO_URL: str
    FRONTEND_URL: str

    RUSTFS_ENDPOINT: str
    RUSTFS_ACCESS_KEY: str
    RUSTFS_SECRET_KEY: str
    RUSTFS_BUCKET_NAME: str
    EXTERNAL_ENDPOINT: str

    REDIS_URL: str

    GEMINI_MODEL: str = "gemini-3.8-flash"

    # Rate limits (per user, or per login name for failed logins)
    UPLOAD_LIMIT_PER_HOUR: int = 30
    DISCUSSION_MESSAGE_LIMIT_PER_MINUTE: int = 10
    LOGIN_FAILURE_LIMIT: int = 10
    LOGIN_FAILURE_WINDOW_SECONDS: int = 15 * 60

    DEFAULT_ADMIN_NAME: str
    DEFAULT_ADMIN_PASSWORD: str
    DEFAULT_ADMIN_EMAIL: str

    @field_validator("SECRET_KEY")
    @classmethod
    def _check_secret_key(cls, value: str) -> str:
        # Signs every JWT; an empty key would make tokens forgeable
        if not value.strip():
            raise ValueError("SECRET_KEY must be set (e.g. `openssl rand -hex 32`)")
        if len(value) < 32:
            logger.warning("SECRET_KEY is shorter than 32 characters")
        return value

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
