"""Notification schemas for API serialization."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class NotificationResponse(BaseModel):
    """Notification response schema."""
    id: str
    type: str  # e.g., "friend_request"
    message: str
    sender_id: int
    sender_username: str
    created_at: datetime
    ref_id: str  # Reference UUID (e.g., friendship_id)

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Notification list response schema."""
    notifications: List[NotificationResponse]
    message: str

    class Config:
        from_attributes = True
