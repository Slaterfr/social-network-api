"""Vote repository for post vote-specific database queries."""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models
from .base import BaseCRUD


class VoteRepository(BaseCRUD[models.Vote]):
    """Vote repository for post votes with specialized queries."""
    
    def __init__(self):
        super().__init__(models.Vote)
    
    def find_vote(
        self, db: Session, post_id: int, user_id: int
    ) -> Optional[models.Vote]:
        """Find a vote by post and user."""
        return db.query(self.model).filter(
            (self.model.post_id == post_id) & (self.model.user_id == user_id)
        ).first()
    
    def user_voted_on_post(
        self, db: Session, post_id: int, user_id: int
    ) -> bool:
        """Check if a user has voted on a post."""
        return self.find_vote(db, post_id, user_id) is not None
    
    def get_vote_count(self, db: Session, post_id: int) -> int:
        """Get total vote count (number of likes) for a post."""
        return db.query(func.count(self.model.user_id)).filter(
            self.model.post_id == post_id
        ).scalar() or 0
    
    def get_post_votes(
        self, db: Session, post_id: int
    ):
        """Get all votes for a post."""
        return db.query(self.model).filter(
            self.model.post_id == post_id
        ).all()
    
    def get_user_votes(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 100
    ):
        """Get all votes by a user."""
        return db.query(self.model).filter(
            self.model.user_id == user_id
        ).offset(skip).limit(limit).all()
    
    def get_vote_count_by_user(self, db: Session, user_id: int) -> int:
        """Get total number of votes given by a user."""
        return db.query(func.count(self.model.post_id)).filter(
            self.model.user_id == user_id
        ).scalar() or 0
