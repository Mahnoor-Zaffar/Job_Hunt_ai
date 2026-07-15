"""File storage abstraction — local filesystem and S3-compatible backends.

Provides a simple ``read`` / ``write`` / ``delete`` / ``exists``
interface so that resume uploads and other file operations are not
coupled to a specific storage backend.
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class StorageBackend(ABC):
    """Abstract file storage backend."""

    @abstractmethod
    async def write(self, key: str, data: bytes, content_type: str = "") -> str: ...

    @abstractmethod
    async def read(self, key: str) -> bytes | None: ...

    @abstractmethod
    async def delete(self, key: str) -> bool: ...

    @abstractmethod
    async def exists(self, key: str) -> bool: ...


class LocalStorage(StorageBackend):
    """Stores files on the local filesystem.

    Suitable for development and single-server deployments.
    """

    def __init__(self, base_dir: str = "uploads") -> None:
        self._base = Path(base_dir).resolve()
        self._base.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe = "/".join(key.split("/")[-3:]) if "/" in key else key
        target = self._base / safe.lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    async def write(self, key: str, data: bytes, content_type: str = "") -> str:
        path = self._path(key)
        path.write_bytes(data)
        return str(path)

    async def read(self, key: str) -> bytes | None:
        path = self._path(key)
        if path.exists():
            return path.read_bytes()
        return None

    async def delete(self, key: str) -> bool:
        path = self._path(key)
        if path.exists():
            path.unlink()
            return True
        return False

    async def exists(self, key: str) -> bool:
        return self._path(key).exists()


class S3Storage(StorageBackend):
    """Stores files in an S3-compatible object store.

    Requires ``boto3`` to be installed.
    """

    def __init__(
        self,
        bucket: str,
        *,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        region: str = "us-east-1",
    ) -> None:
        self._bucket = bucket
        self._endpoint = endpoint_url
        self._access = access_key or os.getenv("AWS_ACCESS_KEY_ID", "")
        self._secret = secret_key or os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self._region = region

    def _client(self) -> Any:
        import boto3

        return boto3.client(
            "s3",
            endpoint_url=self._endpoint,
            aws_access_key_id=self._access,
            aws_secret_access_key=self._secret,
            region_name=self._region,
        )

    async def write(self, key: str, data: bytes, content_type: str = "") -> str:
        client = self._client()
        client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type or "application/octet-stream",
        )
        return f"s3://{self._bucket}/{key}"

    async def read(self, key: str) -> bytes | None:
        try:
            client = self._client()
            resp = client.get_object(Bucket=self._bucket, Key=key)
            return resp["Body"].read()  # type: ignore[no-any-return]
        except Exception:
            return None

    async def delete(self, key: str) -> bool:
        try:
            client = self._client()
            client.delete_object(Bucket=self._bucket, Key=key)
            return True
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        try:
            client = self._client()
            client.head_object(Bucket=self._bucket, Key=key)
            return True
        except Exception:
            return False


def get_storage() -> StorageBackend:
    """Factory that returns the configured storage backend.

    Set ``FILE_STORAGE_BACKEND=s3`` and the required S3 env vars to
    use S3; otherwise defaults to local storage.
    """
    backend = os.getenv("FILE_STORAGE_BACKEND", "local")
    if backend == "s3":
        return S3Storage(
            bucket=os.getenv("S3_BUCKET", "job-hunting-uploads"),
            endpoint_url=os.getenv("S3_ENDPOINT_URL"),
            region=os.getenv("S3_REGION", "us-east-1"),
        )
    return LocalStorage(base_dir=os.getenv("FILE_STORAGE_DIR", "uploads"))
