from datetime import timedelta

from types import SimpleNamespace

from app.utils import storage


class FakeMinio:
    def __init__(self, *, exists=False):
        self.exists = exists
        self.called_make_bucket = False

    def bucket_exists(self, bucket):
        return self.exists

    def make_bucket(self, bucket):
        self.called_make_bucket = True

    def presigned_get_object(self, bucket_name, object_name, expires):
        return f"http://{storage.settings.MINIO_ENDPOINT}/{bucket_name}/{object_name}?expires={int(expires.total_seconds())}"


def test_get_minio_client_creates_bucket(monkeypatch):
    fake = FakeMinio()
    monkeypatch.setattr(storage, "_minio_client", None)
    monkeypatch.setattr(storage, "Minio", lambda *args, **kwargs: fake)

    client = storage.get_minio_client()
    assert client is fake
    assert fake.called_make_bucket is True


def test_presigned_get_url_rewrites_endpoint(monkeypatch):
    fake = FakeMinio(exists=True)
    monkeypatch.setattr(storage, "_minio_client", fake)

    url = storage.presigned_get_url("path/to/file.pdf", expires=timedelta(minutes=10))
    assert url.startswith(storage.settings.EXTERNAL_ENDPOINT)
    assert "path/to/file.pdf" in url
