from abc import ABC, abstractmethod


class ObjectStorageAdapter(ABC):
    """Rule: every object-storage backend implements this interface, so
    services depend on the abstraction rather than a specific backend (same
    pattern as app/integrations/base.py). S3StorageAdapter is the production
    implementation; LocalFilesystemStorageAdapter is a dev/test fallback
    used when no S3 bucket is configured — see get_storage_adapter().
    """

    @abstractmethod
    def upload(self, *, key: str, content: bytes, content_type: str) -> str:
        """Stores content under key. Returns a reference (URL or URI) that
        download() can later use to retrieve it — callers must treat this as
        opaque and persist it verbatim (e.g. in ImportJob.file_url).
        """
        ...

    @abstractmethod
    def download(self, file_url: str) -> bytes:
        """Retrieves content previously stored via upload(), given the
        reference upload() returned.
        """
        ...
