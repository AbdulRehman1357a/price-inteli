from pathlib import Path

from app.storage.base import ObjectStorageAdapter


class LocalFilesystemStorageAdapter(ObjectStorageAdapter):
    """Dev/test fallback used when no S3 bucket is configured, so imports
    work out of the box without requiring real AWS infrastructure. Selected
    automatically by get_storage_adapter() — never used when
    S3_BUCKET_NAME is set.
    """

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def upload(self, *, key: str, content: bytes, content_type: str) -> str:
        del content_type  # unused; local filesystem has no content-type metadata
        path = self._base_dir / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return f"file://{path.resolve().as_posix()}"

    def download(self, file_url: str) -> bytes:
        prefix = "file://"
        if not file_url.startswith(prefix):
            raise ValueError(f"Not a local file reference: {file_url}")
        return Path(file_url[len(prefix) :]).read_bytes()
