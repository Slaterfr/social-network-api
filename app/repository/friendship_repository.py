"""Friendship repository for friendship-specific database queries."""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app import models
from .base import BaseCRUD


class FriendshipRepository(BaseCRUD[models.Friendship]):
    """Friendship repository with specialized queries."""
    
    def __init__(self):
        super().__init__(models.Friendship)
        
    def find_friendship(
        self, db: Session, requestor_id: int, requested_id: int
    ) -> Optional[models.Friendship]:
        """Find specific friendship request from requestor to requested."""
        return db.query(self.model).filter(
            (self.model.requestor_id == requestor_id) & 
            (self.model.requested_id == requested_id)
        ).first()

    def find_friendship_bidirectional(
        self, db: Session, user_a: int, user_b: int
    ) -> Optional[models.Friendship]:
        """Find friendship request or status between two users in either direction."""
        return db.query(self.model).filter(
            or_(
                (self.model.requestor_id == user_a) & (self.model.requested_id == user_b),
                (self.model.requestor_id == user_b) & (self.model.requested_id == user_a)
            )
        ).first()

    def get_user_friends(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.Friendship]:
        """Get all accepted friendships for a user."""
        return db.query(self.model).filter(
            (self.model.status == "accepted") & 
            (or_(self.model.requestor_id == user_id, self.model.requested_id == user_id))
        ).offset(skip).limit(limit).all()

    def get_pending_requests_sent(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.Friendship]:
        """Get pending friendship requests sent by a user."""
        return db.query(self.model).filter(
            (self.model.requestor_id == user_id) & 
            (self.model.status == "pending")
        ).offset(skip).limit(limit).all()

    def get_pending_requests_received(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.Friendship]:
        """Get pending friendship requests received by a user."""
        return db.query(self.model).filter(
            (self.model.requested_id == user_id) & 
            (self.model.status == "pending")
        ).offset(skip).limit(limit).all()
