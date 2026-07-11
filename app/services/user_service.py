"""User service layer - handles user profile and management operations."""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile

from app import schemas, models
from app.repository.user_repository import UserRepository
from app.dependencies.security import hash_password, verify_password
from .file_management import FileManagementService


class UserService:
    """User service for profile and account management."""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.file_management = FileManagementService()
    
    def get_user(self, user_id: int, db: Session) -> models.User:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            User model
            
        Raises:
            HTTPException: If user not found
        """
        user = self.user_repo.read(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        return self.attach_avatar_url(user)
    
    def get_user_by_username(self, username: str, db: Session) -> list[models.User]:
        """
        Get users matching username pattern.
        
        Args:
            username: Username pattern
            db: Database session
            
        Returns:
            List of matching User models
        """
        users = self.user_repo.find_by_username(db, username)
        return [self.attach_avatar_url(user) for user in users]
    
    def update_profile(
        self, user_id: int, update_data: schemas.UserUpdate, db: Session
    ) -> models.User:
        """
        Update user profile information.
        
        Args:
            user_id: User ID
            update_data: Update data (bio, username, etc.)
            db: Database session
            
        Returns:
            Updated user model
            
        Raises:
            HTTPException: If user not found or validation fails
        """
        user = self.get_user(user_id, db)
        
        # Check if new username is taken (if being changed)
        if update_data.username and update_data.username != user.username:
            if self.user_repo.username_exists(db, update_data.username):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already taken"
                )
        
        # Update allowed fields
        update_dict = update_data.dict(exclude_unset=True)
        
        # Remove fields that shouldn't be updated through profile endpoint
        if "password" in update_dict:
            del update_dict["password"]
        if "email" in update_dict:
            del update_dict["email"]
        if "role" in update_dict:
            del update_dict["role"]
        
        updated_user = self.user_repo.update(db, user_id, update_dict)
        return self.attach_avatar_url(updated_user)
    
    def change_password(
        self, user_id: int, old_password: str, new_password: str, db: Session
    ) -> models.User:
        """
        Change user password with old password verification.
        
        Args:
            user_id: User ID
            old_password: Current password (plain)
            new_password: New password (plain)
            db: Database session
            
        Returns:
            Updated user model
            
        Raises:
            HTTPException: If user not found or old password doesn't match
        """
        user = self.get_user(user_id, db)
        
        # Verify old password
        if not verify_password(old_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Hash and update new password
        hashed_new_password = hash_password(new_password)
        updated_user = self.user_repo.update(
            db, user_id, {"password": hashed_new_password}
        )
        
        return updated_user
    
    def user_exists(self, user_id: int, db: Session) -> bool:
        """Check if user exists."""
        return self.user_repo.read(db, user_id) is not None

    def attach_avatar_url(self, user: models.User) -> models.User:
        """Attach presigned avatar download URL if uploader has an avatar."""
        if user and user.avatar:
            try:
                user.avatar_url = self.file_management.generate_url(user.avatar.storage_key)
            except Exception:
                user.avatar_url = None
        elif user:
            user.avatar_url = None
        return user

    async def update_avatar(self, user: models.User, file: UploadFile, db: Session) -> models.User:
        """Upload a new profile picture, clean up the old one, and update references."""
        # Upload the new image to S3 under folder "avatars"
        new_media = await self.file_management.upload_file(file, "avatars", user.id, db)
        
        # If user has an old avatar, delete it from S3 and clean up DB references
        old_avatar_id = user.avatar_id
        if old_avatar_id:
            try:
                self.file_management.delete_file(old_avatar_id, db)
            except Exception as e:
                # Log and skip, old avatar might not exist in S3/DB
                print(f"Warning: Failed to clean up old avatar: {str(e)}")

        # Set the new avatar ID and commit
        user.avatar_id = new_media.id
        db.add(user)
        db.commit()
        db.refresh(user)

        return self.attach_avatar_url(user)
