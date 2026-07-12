"""Schema layer - Pydantic models for request/response validation."""

# Common schemas
from .common import TokenData, Token, ErrorResponse, PaginationParams, RefreshTokenRequest

# User schemas
from .user_schemas import (
    UserCreate,
    UserLogin,
    UserUpdate,
    UserChangePassword,
    UserResponse,
    UserPublicProfile,
)

# Post schemas
from .post_schemas import (
    PostBase,
    PostCreate,
    PostUpdate,
    PostResponse,
    PostWithStats,
    PostListResponse,
)

# Comment schemas
from .comment_schemas import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentWithReplies,
    CommentListResponse,
)

# Vote schemas
from .vote_schemas import (
    VoteCreate,
    VoteResponse,
    CommentVoteCreate,
    CommentVoteResponse,
    VoteStats,
    CommentVoteStats,
)

# Friendship schemas
from .friendship_schemas import (
    FriendshipCreate,
    FriendshipUpdate,
    FriendshipResponse,
)

# Notification schemas
from .notification_schemas import (
    NotificationResponse,
    NotificationListResponse,
)

__all__ = [
    # Common
    "TokenData",
    "Token",
    "ErrorResponse",
    "PaginationParams",
    "RefreshTokenRequest",
    # User
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserChangePassword",
    "UserResponse",
    "UserPublicProfile",
    # Post
    "PostBase",
    "PostCreate",
    "PostUpdate",
    "PostResponse",
    "PostWithStats",
    "PostListResponse",
    # Comment
    "CommentCreate",
    "CommentUpdate",
    "CommentResponse",
    "CommentWithReplies",
    "CommentListResponse",
    # Vote
    "VoteCreate",
    "VoteResponse",
    "CommentVoteCreate",
    "CommentVoteResponse",
    "VoteStats",
    "CommentVoteStats",
    # Friendship
    "FriendshipCreate",
    "FriendshipUpdate",
    "FriendshipResponse",
    # Notification
    "NotificationResponse",
    "NotificationListResponse",
]
