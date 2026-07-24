from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
from datetime import datetime
from .user_schemas import UserPublicProfile

class CommunityBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    slogan: Optional[str] = Field(default=None, max_length=200)
    privacy: str = Field(default="public")

class CommunityCreate(CommunityBase):
    pass

class CommunityResponse(CommunityBase):
    id: uuid.UUID
    owner_id: int
    avatar_url: Optional[str] = None
    created_at: datetime
    modified_at: Optional[datetime] = None
    member_count: int = 0
    role_in_community: Optional[str] = None
    join_request_status: Optional[str] = None

    class Config:
        from_attributes = True

class CommunityMemberResponse(BaseModel):
    user_id: int
    community_id: uuid.UUID
    community_role: str
    status: str
    joined_date: datetime
    user: UserPublicProfile

    class Config:
        from_attributes = True

class MemberRoleUpdate(BaseModel):
    community_role: str = Field(...)

class CommunityMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    reply_to_message_id: Optional[uuid.UUID] = None
    message_type: str = Field(default="text")

class CommunityMessageResponse(BaseModel):
    id: uuid.UUID
    community_id: uuid.UUID
    issuer_id: int
    content: str
    reply_to_message_id: Optional[uuid.UUID] = None
    message_type: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: UserPublicProfile
    replied_to_message_content: Optional[str] = None
    replied_to_message_username: Optional[str] = None

    class Config:
        from_attributes = True

class CommunityJoinRequestResponse(BaseModel):
    id: uuid.UUID
    user_id: int
    community_id: uuid.UUID
    status: str
    created_at: datetime
    user: UserPublicProfile

    class Config:
        from_attributes = True

class JoinRequestAction(BaseModel):
    status: str = Field(...)
