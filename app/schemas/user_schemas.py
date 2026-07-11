"""User schemas for input/output validation."""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    bio: Optional[str] = Field(default=None, max_length=500)


class UserCreate(UserBase):
    """User creation schema with password validation."""
    password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """User login schema."""
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """User profile update schema."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    bio: Optional[str] = Field(None, max_length=500)


class UserChangePassword(BaseModel):
    """Change password schema."""
    old_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserResponse(UserBase):
    """User response schema."""
    id: int
    role: str
    created_at: datetime
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserPublicProfile(BaseModel):
    """Public user profile (limited info)."""
    id: int
    username: str
    bio: Optional[str]
    created_at: datetime
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True
