"""Comment service layer - handles comment CRUD with authorization."""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy import func

from app import schemas, models
from app.repository.comment_repository import CommentRepository
from app.repository.post_repository import PostRepository
from .file_management import FileManagementService


class CommentService:
    """Comment service for CRUD operations and authorization."""
    
    def __init__(self):
        self.comment_repo = CommentRepository()
        self.post_repo = PostRepository()
        self.file_management = FileManagementService()
    
    def create_comment(
        self, comment_data: schemas.CommentCreate, user_id: int, db: Session
    ) -> models.Comment:
        """
        Create a new comment.
        
        Args:
            comment_data: Comment data
            user_id: ID of comment author (current user)
            db: Database session
            
        Returns:
            Created comment model
            
        Raises:
            HTTPException: If post doesn't exist
        """
        # Verify post exists
        if not self.post_repo.read(db, comment_data.post_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post with id {comment_data.post_id} not found"
            )
        
        # If replying to a comment, verify parent exists
        if comment_data.parent_id:
            parent = self.comment_repo.read(db, comment_data.parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parent comment with id {comment_data.parent_id} not found"
                )
        
        comment = self.comment_repo.create(
            db,
            {
                "content": comment_data.content,
                "post_id": comment_data.post_id,
                "user_id": user_id,
                "parent_id": comment_data.parent_id
            }
        )
        return self._attach_comment_avatar(comment, db)
    
    def get_comment(self, comment_id: int, db: Session) -> models.Comment:
        """
        Get comment by ID.
        
        Args:
            comment_id: Comment ID
            db: Database session
            
        Returns:
            Comment model
            
        Raises:
            HTTPException: If comment not found
        """
        comment = self.comment_repo.read(db, comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment with id {comment_id} not found"
            )
        return self._attach_comment_avatar(comment, db)
    
    def get_post_comments(
        self, post_id: int, db: Session, current_user: Optional[models.User] = None, skip: int = 0, limit: int = 20
    ) -> List[models.Comment]:
        """
        Get all comments for a post.
        
        Args:
            post_id: Post ID
            db: Database session
            current_user: Optional current logged in user
            skip: Number of records to skip
            limit: Max records to return
            
        Returns:
            List of comments
        """
        current_user_id = current_user.id if current_user else None
        comments = self.comment_repo.find_by_post_with_stats(db, post_id, current_user_id, skip, limit)
        return [self._attach_comment_avatar(c, db, current_user) for c in comments]
    
    def get_comment_replies(self, comment_id: int, db: Session, current_user: Optional[models.User] = None) -> List[models.Comment]:
        """
        Get all replies to a comment.
        """
        current_user_id = current_user.id if current_user else None
        replies = self.comment_repo.find_replies_with_stats(db, comment_id, current_user_id)
        return [self._attach_comment_avatar(c, db, current_user) for c in replies]
    
    def update_comment(
        self, comment_id: int, current_user: models.User, update_data: schemas.CommentUpdate, db: Session
    ) -> models.Comment:
        """
        Update comment with authorization check.
        """
        comment = self.get_comment(comment_id, db)
        
        # Check authorization: owner or admin
        if comment.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this comment"
            )
        
        data_to_update = update_data.dict(exclude_unset=True)
        data_to_update["updated_at"] = datetime.now(timezone.utc)
        
        updated_comment = self.comment_repo.update(
            db, comment_id, data_to_update
        )
        comment_with_stats = self.comment_repo.find_by_id_stats(db, comment_id, current_user.id)
        return self._attach_comment_avatar(comment_with_stats or updated_comment, db, current_user)
    
    def delete_comment(self, comment_id: int, current_user: models.User, db: Session) -> bool:
        """
        Delete comment with authorization check.
        
        Args:
            comment_id: Comment ID
            current_user: User object making request (authorization)
            db: Database session
            
        Returns:
            True if deleted
            
        Raises:
            HTTPException: If comment not found or user not authorized
        """
        comment = self.get_comment(comment_id, db)
        
        # Check authorization: owner or admin
        if comment.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this comment"
            )
        
        return self.comment_repo.delete(db, comment_id)
    
    def comment_exists(self, comment_id: int, db: Session) -> bool:
        """Check if comment exists."""
        return self.comment_repo.read(db, comment_id) is not None

    def _attach_comment_avatar(self, comment: models.Comment, db: Session, current_user: Optional[models.User] = None) -> models.Comment:
        """Attach presigned avatar download URL and stats to the comment."""
        if not comment:
            return comment
            
        if comment.user:
            if comment.user.avatar:
                try:
                    comment.user.avatar_url = self.file_management.generate_url(comment.user.avatar.storage_key)
                except Exception:
                    comment.user.avatar_url = None
            else:
                comment.user.avatar_url = None
                
        # Ensure properties exist
        if not hasattr(comment, 'vote_count'):
            comment.vote_count = 0
        if not hasattr(comment, 'user_voted'):
            comment.user_voted = False
                
        return comment
