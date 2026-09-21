from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.storage.base import ObjectStorageAdapter
from app.storage.local import LocalFilesystemStorageAdapter


@lru_cache
def get_storage_adapter() -> ObjectStorageAdapter:
    settings = get_settings()
    if settings.s3_bucket_name:
        from app.storage.s3 import S3StorageAdapter  # lazy: boto3 only needed when S3 is configured

        return S3StorageAdapter()
    return LocalFilesystemStorageAdapter(Path(settings.local_storage_dir))
