from datetime import timedelta

from minio import Minio

from app.core.config import settings

_storage_client = None


def get_storage_client() -> Minio:
    global _storage_client
    if _storage_client is None:
        _storage_client = Minio(
            endpoint=settings.RUSTFS_ENDPOINT,
            access_key=settings.RUSTFS_ACCESS_KEY,
            secret_key=settings.RUSTFS_SECRET_KEY,
            secure=False,
        )
        if not _storage_client.bucket_exists(settings.RUSTFS_BUCKET_NAME):
            _storage_client.make_bucket(settings.RUSTFS_BUCKET_NAME)
    return _storage_client


def presigned_get_url(
    object_name: str, expires: timedelta = timedelta(hours=1)
) -> str:
    """
    Get a presigned GET URL for frontend to download/preview PDF files.
    """
    client = get_storage_client()
    presigned_url = client.presigned_get_object(
        bucket_name=settings.RUSTFS_BUCKET_NAME,
        object_name=object_name,
        expires=expires
    )

    presigned_url = presigned_url.replace(
        f"http://{settings.RUSTFS_ENDPOINT}",
        f"{settings.EXTERNAL_ENDPOINT}",
        1
    )

    return presigned_url
