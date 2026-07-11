import boto3
from typing import Optional
from app.core.config import Config


class S3StorageService:
    """Service to handle S3 bucket direct client interactions."""

    def __init__(self):
        self.client = boto3.client(
            "s3",
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_REGION
        )
        self.bucket = Config.AWS_BUCKET_NAME

    def upload_file(self, file_data: bytes, key: str, content_type: str = "image/webp") -> None:
        """
        Upload raw file bytes directly to the S3 bucket.
        """
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=file_data,
            ContentType=content_type
        )

    def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned GET URL for a private S3 object.
        """
        return self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': key},
            ExpiresIn=expiration
        )

    def delete_file(self, key: str) -> None:
        """
        Delete an object from S3.
        """
        self.client.delete_object(
            Bucket=self.bucket,
            Key=key
        )