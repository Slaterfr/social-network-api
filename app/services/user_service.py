"""User service layer - handles user profile and management operations."""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app import schemas, models
from app.repository.user_repository import UserRepository
from app.dependencies.security import hash_password, verify_password


class UserService:
    """User service for profile and account management."""
    
    def __init__(self):
        self.user_repo = UserRepository()
    
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
        return user
    
    def get_user_by_username(self, username: str, db: Session) -> models.User:
        """
        Get user by username.
        
        Args:
            username: Username
            db: Database session
            
        Returns:
            User model
            
        Raises:
            HTTPException: If user not found
        """
        user = self.user_repo.find_by_username(db, username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {username} not found"
            )
        return user
    
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
        return updated_user
    
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
