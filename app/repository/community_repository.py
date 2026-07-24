from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
import uuid

from app import models
from .base import BaseCRUD

class CommunityRepository(BaseCRUD[models.Community]):
    def __init__(self):
        super().__init__(models.Community)

    def find_all_public(self, db: Session, skip: int = 0, limit: int = 100) -> List[models.Community]:
        return db.query(self.model).filter(
            self.model.deleted_at.is_(None),
            self.model.privacy != "private"
        ).order_by(desc(self.model.created_at)).offset(skip).limit(limit).all()

    def get_member_count(self, db: Session, community_id: uuid.UUID) -> int:
        return db.query(func.count(models.CommunityMember.user_id)).filter(
            models.CommunityMember.community_id == community_id,
            models.CommunityMember.status == "active"
        ).scalar() or 0

    def get_member_role(self, db: Session, community_id: uuid.UUID, user_id: int) -> Optional[str]:
        member = db.query(models.CommunityMember).filter(
            models.CommunityMember.community_id == community_id,
            models.CommunityMember.user_id == user_id,
            models.CommunityMember.status == "active"
        ).first()
        return member.community_role if member else None

    def get_join_request_status(self, db: Session, community_id: uuid.UUID, user_id: int) -> Optional[str]:
        req = db.query(models.CommunityJoinRequest).filter(
            models.CommunityJoinRequest.community_id == community_id,
            models.CommunityJoinRequest.user_id == user_id
        ).order_by(desc(models.CommunityJoinRequest.created_at)).first()
        return req.status if req else None

    def find_user_communities(self, db: Session, user_id: int) -> List[models.Community]:
        return db.query(self.model).join(
            models.CommunityMember,
            models.CommunityMember.community_id == self.model.id
        ).filter(
            models.CommunityMember.user_id == user_id,
            models.CommunityMember.status == "active",
            self.model.deleted_at.is_(None)
        ).all()

    def find_members(self, db: Session, community_id: uuid.UUID) -> List[models.CommunityMember]:
        return db.query(models.CommunityMember).filter(
            models.CommunityMember.community_id == community_id,
            models.CommunityMember.status == "active"
        ).all()

    def find_messages(self, db: Session, community_id: uuid.UUID, limit: int = 50) -> List[models.CommunityMessage]:
        # Return in ascending order for chat timeline
        messages = db.query(models.CommunityMessage).filter(
            models.CommunityMessage.community_id == community_id,
            models.CommunityMessage.deleted_at.is_(None)
        ).order_by(desc(models.CommunityMessage.created_at)).limit(limit).all()
        messages.reverse()
        return messages

    def find_join_requests(self, db: Session, community_id: uuid.UUID) -> List[models.CommunityJoinRequest]:
        return db.query(models.CommunityJoinRequest).filter(
            models.CommunityJoinRequest.community_id == community_id,
            models.CommunityJoinRequest.status == "pending"
        ).all()
