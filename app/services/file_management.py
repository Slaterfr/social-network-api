"""File management service layer - handles PIL image processing, S3 upload/deletion, and presigned URLs."""

import uuid
from io import BytesIO
from PIL import Image
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status
from typing import Optional

from app import models
from app.core.boto_client import S3StorageService
from app.repository.media_repository import MediaRepository
from app.core.config import Config


class FileManagementService:
    """Service to handle image conversion, S3 file storage, and DB persistence."""

    def __init__(self):
        self.s3_service = S3StorageService()
        self.media_repo = MediaRepository()

    async def upload_file(
        self, file: UploadFile, folder: str, user_id: int, db: Session
    ) -> models.MediaFile:
        """
        Validate, compress to .webp, upload to S3, and save record in the DB.
        """
        # Validate mime type
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed"
            )

        # Read file bytes
        file_bytes = await file.read()

        # Validate file size (5MB limit)
        MAX_SIZE = 5 * 1024 * 1024  # 5 Megabytes
        if len(file_bytes) > MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds the maximum limit of 5MB"
            )

        # Verify image validity and convert to WebP format
        try:
            image = Image.open(BytesIO(file_bytes))
            
            # Convert RGBA to RGB if saving to WebP (avoids transparent boundary compression artifacts)
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
                
            output_buffer = BytesIO()
            image.save(output_buffer, format="WEBP", quality=80)
            webp_data = output_buffer.getvalue()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image file format: {str(e)}"
            )

        # Generate unique storage key and standard public-facing base URL
        unique_id = uuid.uuid4()
        storage_key = f"{folder}/{unique_id}.webp"
        
        # Build default base URL
        if Config.AWS_PUBLIC_BASE_URL:
            base_url = Config.AWS_PUBLIC_BASE_URL.rstrip('/')
            url = f"{base_url}/{storage_key}"
        else:
            url = f"https://{Config.AWS_BUCKET_NAME}.s3.{Config.AWS_REGION}.amazonaws.com/{storage_key}"

        # Upload to S3
        try:
            self.s3_service.upload_file(webp_data, storage_key, content_type="image/webp")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to S3: {str(e)}"
            )

        # Create MediaFile DB record
        try:
            media_record = self.media_repo.create(
                db,
                {
                    "id": unique_id,
                    "storage_key": storage_key,
                    "url": url,
                    "uploaded_by": user_id
                }
            )
            return media_record
        except Exception as e:
            # Cleanup uploaded file from S3 if DB save fails
            try:
                self.s3_service.delete_file(storage_key)
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to record file in database: {str(e)}"
            )

    def generate_url(self, storage_key: str, expiration: int = 3600) -> str:
        """
        Generate a temporary presigned URL for private bucket downloads.
        """
        try:
            return self.s3_service.generate_presigned_url(storage_key, expiration)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate presigned download URL: {str(e)}"
            )

    def delete_file(self, media_id: uuid.UUID, db: Session) -> bool:
        """
        Delete file from S3 and remove its reference record from the database.
        """
        media = self.media_repo.read(db, media_id)
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file record not found"
            )

        # Delete from S3
        try:
            self.s3_service.delete_file(media.storage_key)
        except Exception as e:
            # We can log and continue to delete the DB record if the file is missing from S3
            print(f"Warning: Failed to delete file from S3 storage: {str(e)}")

        # Delete DB reference
        return self.media_repo.delete(db, media_id)
