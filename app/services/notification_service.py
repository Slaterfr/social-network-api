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
        Currently lists pending friend requests received by the user.
        """
        # Fetch pending requests received by this user
        pending_requests = self.friendship_repo.get_pending_requests_received(
            db, user_id, skip, limit
        )

        notifications = []
        for req in pending_requests:
            # Find the sender (requestor) to get their username
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

        message = "No new notifications" if not notifications else f"You have {len(notifications)} notifications"
        return schemas.NotificationListResponse(
            notifications=notifications,
            message=message
        )
