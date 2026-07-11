"""Post schemas for input/output validation."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import uuid
from datetime import datetime
from .user_schemas import UserPublicProfile


class PostBase(BaseModel):
    """Base post schema with common fields."""
    title: str = Field(..., min_length=3, max_length=200)
    content: str = Field(..., min_length=5, max_length=5000)
    published: bool = Field(default=True)


class PostCreate(PostBase):
    """Post creation schema."""
    media_ids: Optional[List[uuid.UUID]] = Field(default=None)


class PostUpdate(BaseModel):
    """Post update schema."""
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    content: Optional[str] = Field(None, min_length=10, max_length=5000)
    published: Optional[bool] = None


class PostResponse(PostBase):
    """Post response schema."""
    id: int
    owner_id: int
    owner: UserPublicProfile
    created_at: datetime
    updated_at: Optional[datetime] = None
    media_urls: List[str] = []
    
    class Config:
        from_attributes = True


class PostWithStats(PostResponse):
    """Post response with engagement stats."""
    vote_count: int = 0
    comment_count: int = 0


class PostListResponse(BaseModel):
    """Post list response."""
    posts: list[PostResponse]
    total: int
    skip: int
    limit: int
