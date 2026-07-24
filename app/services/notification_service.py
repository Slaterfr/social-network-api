"""Notification service layer - handles fetching notifications."""

from typing import List
from sqlalchemy.orm import Session

from app import models, schemas
from app.repository.friendship_repository import FriendshipRepository
from app.repository.user_repository import UserRepository


class NotificationService:
    """Service to handle notification query and transformation logic."""

    def __init__(self):
        self.friendship_repo = FriendshipRepository()
        self.user_repo = UserRepository()

    def get_notifications(
        self, user_id: int, db: Session, skip: int = 0, limit: int = 100
    ) -> schemas.NotificationListResponse:
        """
        Retrieve notifications for the current user.
        Includes pending friend requests and community invitations.
        """
        notifications = []

        # 1. Fetch pending friend requests
        pending_requests = self.friendship_repo.get_pending_requests_received(
            db, user_id, skip, limit
        )
        for req in pending_requests:
            sender = self.user_repo.read(db, req.requestor_id)
            sender_username = sender.username if sender else "Unknown User"

            notifications.append(
                schemas.NotificationResponse(
                    id=str(req.id),
                    type="friend_request",
                    message=f"{sender_username} sent you a friend request",
                    sender_id=req.requestor_id,
                    sender_username=sender_username,
                    created_at=req.created_at,
                    ref_id=str(req.id)
                )
            )

        # 2. Fetch pending community invitations
        community_invites = db.query(models.CommunityJoinRequest).filter(
            models.CommunityJoinRequest.user_id == user_id,
            models.CommunityJoinRequest.status == "invited"
        ).all()
        for invite in community_invites:
            community = db.query(models.Community).filter(
                models.Community.id == invite.community_id,
                models.Community.deleted_at.is_(None)
            ).first()
            if community:
                notifications.append(
                    schemas.NotificationResponse(
                        id=str(invite.id),
                        type="community_invite",
                        message=f"You were invited to join {community.name}",
                        sender_id=community.owner_id,
                        sender_username=community.name,
                        created_at=invite.created_at,
                        ref_id=str(community.id)
                    )
                )

        # Sort notifications by date descending
        notifications.sort(key=lambda x: x.created_at, reverse=True)

        message = "No new notifications" if not notifications else f"You have {len(notifications)} notifications"
        return schemas.NotificationListResponse(
            notifications=notifications,
            message=message
        )
