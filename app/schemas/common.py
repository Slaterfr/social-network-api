"""Common schemas used across the application."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TokenData(BaseModel):
    """Token payload data."""
    id: Optional[int] = None
    role: Optional[str] = None


class Token(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    status_code: int


class PaginationParams(BaseModel):
    """Pagination parameters."""
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=10, ge=1, le=100)
