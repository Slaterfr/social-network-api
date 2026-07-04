"""Comment Vote repository for comment vote-specific database queries."""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models
from .base import BaseCRUD


class CommentVoteRepository(BaseCRUD[models.CommentVote]):
    """Comment Vote repository with specialized queries."""
    
    def __init__(self):
        super().__init__(models.CommentVote)
    
    def find_comment_vote(
        self, db: Session, comment_id: int, user_id: int
    ) -> Optional[models.CommentVote]:
        """Find a vote on a comment by user."""
        return db.query(self.model).filter(
            (self.model.comment_id == comment_id) & (self.model.user_id == user_id)
        ).first()
    
    def user_voted_on_comment(
        self, db: Session, comment_id: int, user_id: int
    ) -> bool:
        """Check if a user has voted on a comment."""
        return self.find_comment_vote(db, comment_id, user_id) is not None
    
    def get_comment_vote_count(self, db: Session, comment_id: int) -> int:
        """Get total vote count (number of likes) for a comment."""
        return db.query(func.count(self.model.user_id)).filter(
            self.model.comment_id == comment_id
        ).scalar() or 0
    
    def get_comment_votes(
        self, db: Session, comment_id: int
    ):
        """Get all votes for a comment."""
        return db.query(self.model).filter(
            self.model.comment_id == comment_id
        ).all()
    
    def get_user_comment_votes(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 100
    ):
        """Get all comment votes by a user."""
        return db.query(self.model).filter(
            self.model.user_id == user_id
        ).offset(skip).limit(limit).all()
    
    def get_user_comment_vote_count(self, db: Session, user_id: int) -> int:
        """Get total number of comment votes given by a user."""
        return db.query(func.count(self.model.comment_id)).filter(
            self.model.user_id == user_id
        ).scalar() or 0
