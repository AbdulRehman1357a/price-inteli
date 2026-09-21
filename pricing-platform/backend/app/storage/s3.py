import boto3

from app.core.config import get_settings
from app.storage.base import ObjectStorageAdapter


class S3StorageAdapter(ObjectStorageAdapter):
    """Production storage backend. Selected automatically by
    get_storage_adapter() whenever S3_BUCKET_NAME is configured — see
    backend/.env.example for AWS_REGION / S3_BUCKET_NAME. Credentials come
    from the standard boto3 chain (env vars, instance profile, etc.), never
    hard-coded here.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._bucket = settings.s3_bucket_name
        self._client = boto3.client("s3", region_name=settings.aws_region)

    def upload(self, *, key: str, content: bytes, content_type: str) -> str:
        self._client.put_object(Bucket=self._bucket, Key=key, Body=content, ContentType=content_type)
        return f"s3://{self._bucket}/{key}"

    def download(self, file_url: str) -> bytes:
        prefix = f"s3://{self._bucket}/"
        if not file_url.startswith(prefix):
            raise ValueError(f"Not an object in this adapter's bucket: {file_url}")
        key = file_url[len(prefix) :]
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return response["Body"].read()
