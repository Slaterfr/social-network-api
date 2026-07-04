"""Comment schemas for input/output validation."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .user_schemas import UserPublicProfile


class CommentBase(BaseModel):
    """Base comment schema."""
    content: str = Field(..., min_length=1, max_length=2000)


class CommentCreate(CommentBase):
    """Comment creation schema."""
    post_id: int = Field(..., gt=0)
    parent_id: Optional[int] = Field(None, gt=0)


class CommentUpdate(BaseModel):
    """Comment update schema."""
    content: str = Field(..., min_length=1, max_length=2000)


class CommentResponse(CommentBase):
    """Comment response schema."""
    id: int
    post_id: int
    user_id: int
    parent_id: Optional[int]
    user: UserPublicProfile
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CommentWithReplies(CommentResponse):
    """Comment response with nested replies."""
    replies: list["CommentWithReplies"] = []


# Update forward references
CommentWithReplies.model_rebuild()


class CommentListResponse(BaseModel):
    """Comment list response."""
    comments: list[CommentResponse]
    total: int
    skip: int
    limit: int
