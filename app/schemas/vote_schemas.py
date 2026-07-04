"""Vote schemas for input/output validation."""

from pydantic import BaseModel, Field


class VoteCreate(BaseModel):
    """Vote (like) creation schema for posts."""
    post_id: int = Field(..., gt=0)


class VoteResponse(BaseModel):
    """Vote response."""
    message: str


class CommentVoteCreate(BaseModel):
    """Vote (like) creation schema for comments."""
    comment_id: int = Field(..., gt=0)


class CommentVoteResponse(BaseModel):
    """Comment vote response."""
    message: str


class VoteStats(BaseModel):
    """Vote statistics response."""
    post_id: int
    vote_count: int
    user_voted: bool = False


class CommentVoteStats(BaseModel):
    """Comment vote statistics response."""
    comment_id: int
    vote_count: int
    user_voted: bool = False
