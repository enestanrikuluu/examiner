import boto3
from botocore.config import Config as BotoConfig

from src.core.config import settings

s3_client = boto3.client(
    "s3",
    endpoint_url=f"{'https' if settings.minio_use_ssl else 'http'}://{settings.minio_endpoint}",
    aws_access_key_id=settings.minio_access_key,
    aws_secret_access_key=settings.minio_secret_key,
    config=BotoConfig(signature_version="s3v4"),
    region_name="us-east-1",
)


def ensure_bucket_exists() -> None:
    try:
        s3_client.head_bucket(Bucket=settings.minio_bucket)
    except Exception:
        s3_client.create_bucket(Bucket=settings.minio_bucket)
