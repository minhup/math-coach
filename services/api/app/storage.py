from dataclasses import dataclass
from datetime import timedelta
from functools import lru_cache

from minio import Minio
from minio.datatypes import Object
from minio.error import S3Error

from app.config import get_settings


@dataclass(frozen=True)
class StoredObject:
    size: int
    content_type: str


class ObjectNotFoundError(Exception):
    pass


class ObjectStorage:
    def __init__(self) -> None:
        settings = get_settings()
        access_key = settings.object_storage_access_key.get_secret_value()
        secret_key = settings.object_storage_secret_key.get_secret_value()
        self._bucket = settings.object_storage_bucket
        self._internal = Minio(
            settings.object_storage_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=settings.object_storage_secure,
        )
        self._public = Minio(
            settings.object_storage_public_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=settings.object_storage_public_secure,
        )

    def ensure_bucket(self) -> None:
        if not self._internal.bucket_exists(self._bucket):
            self._internal.make_bucket(self._bucket)

    def presign_put(self, object_key: str, expires_seconds: int) -> str:
        return self._public.presigned_put_object(
            self._bucket,
            object_key,
            expires=timedelta(seconds=expires_seconds),
        )

    def stat(self, object_key: str) -> StoredObject:
        try:
            item: Object = self._internal.stat_object(self._bucket, object_key)
        except S3Error as error:
            if error.code in {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
                raise ObjectNotFoundError from error
            raise
        return StoredObject(size=item.size or 0, content_type=item.content_type or "")

    def remove(self, object_key: str) -> None:
        self._internal.remove_object(self._bucket, object_key)


@lru_cache
def get_object_storage() -> ObjectStorage:
    return ObjectStorage()
