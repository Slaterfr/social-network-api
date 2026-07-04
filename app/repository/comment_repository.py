"""Comment repository for comment-specific database queries."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app import models
from .base import BaseCRUD


class CommentRepository(BaseCRUD[models.Comment]):
    """Comment repository with specialized queries."""
    
    def __init__(self):
        super().__init__(models.Comment)
    
    def find_by_post(
        self, db: Session, post_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.Comment]:
        """Find all comments for a post."""
        return db.query(self.model).filter(
            self.model.post_id == post_id
        ).offset(skip).limit(limit).all()
    
    def find_by_user(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.Comment]:
        """Find all comments by a user."""
        return db.query(self.model).filter(
            self.model.user_id == user_id
        ).offset(skip).limit(limit).all()
    
    def find_top_level_comments(
        self, db: Session, post_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.Comment]:
        """Find top-level comments (no parent) for a post."""
        return db.query(self.model).filter(
            (self.model.post_id == post_id) & (self.model.parent_id == None)
        ).offset(skip).limit(limit).all()
    
    def find_replies(
        self, db: Session, parent_comment_id: int
    ) -> List[models.Comment]:
        """Find all replies to a comment."""
        return db.query(self.model).filter(
            self.model.parent_id == parent_comment_id
        ).all()
    
    def find_comment_thread(
        self, db: Session, comment_id: int
    ) -> Optional[models.Comment]:
        """Find a comment with all its replies (nested)."""
        comment = self.read(db, comment_id)
        if comment:
            comment.replies = self.find_replies(db, comment_id)
        return comment
    
    def find_recent_comments(
        self, db: Session, post_id: int, limit: int = 20
    ) -> List[models.Comment]:
        """Find recent comments for a post ordered by creation date."""
        return db.query(self.model).filter(
            self.model.post_id == post_id
        ).order_by(desc(self.model.created_at)).limit(limit).all()
    
    def user_is_owner(self, db: Session, comment_id: int, user_id: int) -> bool:
        """Check if a user is the owner of a comment."""
        comment = self.read(db, comment_id)
        return comment is not None and comment.user_id == user_id
    
    def find_by_post_and_user(
        self, db: Session, post_id: int, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.Comment]:
        """Find comments by user on a specific post."""
        return db.query(self.model).filter(
            (self.model.post_id == post_id) & (self.model.user_id == user_id)
        ).offset(skip).limit(limit).all()
