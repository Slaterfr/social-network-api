"""Friendship schemas for input/output validation."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class FriendshipCreate(BaseModel):
    """Friendship request creation schema."""
    requested_id: int = Field(..., gt=0)


class FriendshipUpdate(BaseModel):
    """Friendship request status update schema."""
    status: str = Field(..., description="Status must be accepted, rejected, or blocked")


class FriendshipResponse(BaseModel):
    """Friendship response schema."""
    id: UUID
    requestor_id: int
    requested_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
