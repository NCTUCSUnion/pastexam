from minio import Minio
from datetime import timedelta
from app.core.config import settings

_minio_client = None

def get_minio_client() -> Minio:
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=False,
        )
        if not _minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
            _minio_client.make_bucket(settings.MINIO_BUCKET_NAME)
    return _minio_client

def presigned_get_url(object_name: str, expires: timedelta = timedelta(hours=1)) -> str:
    """
    Get a presigned GET URL for frontend to download/preview PDF files.
    """
    client = get_minio_client()
    presigned_url = client.presigned_get_object(
        bucket_name=settings.MINIO_BUCKET_NAME,
        object_name=object_name,
        expires=expires
    )
    
    presigned_url = presigned_url.replace(f"http://{settings.MINIO_ENDPOINT}", f"{settings.EXTERNAL_ENDPOINT}", 1)
    
    return presigned_url 