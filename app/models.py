import uuid
from app.repository.database import Base
import sqlalchemy as sa
import sqlalchemy.orm as so


class Posts(Base):
    __tablename__ = "posts"

    id = sa.Column(sa.Integer, primary_key=True, nullable=False)
    title = sa.Column(sa.String, nullable=False)
    content = sa.Column(sa.String, nullable=False)
    published = sa.Column(sa.Boolean, server_default='True', nullable=False)
    created_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now())
    owner_id = sa.Column(sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner = so.relationship("User")
    number = sa.Column(sa.String, )
    updated_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=True)
    media_attachments = so.relationship("PostMedia", back_populates="post", order_by="PostMedia.order", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"
    id = sa.Column(sa.Integer, primary_key=True, nullable=False)
    email = sa.Column(sa.String, nullable=False, unique=True)
    password = sa.Column(sa.String, nullable=False)
    created_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now())
    username = sa.Column(sa.String, nullable=False, unique=True)
    bio = sa.Column(sa.String, nullable=True)
    role = sa.Column(sa.String, nullable=False, server_default="user")
    avatar_id = sa.Column(sa.UUID(as_uuid=True), sa.ForeignKey("media_files.id", ondelete="SET NULL", use_alter=True, name="fk_user_avatar"), nullable=True)
    avatar = so.relationship("MediaFile", foreign_keys=[avatar_id])

class Vote(Base):
    __tablename__ = "votes"
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    post_id = sa.Column(sa.Integer, sa.ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)

class Comment(Base):
    __tablename__ = "comments"
    id = sa.Column(sa.Integer, primary_key=True, nullable=False)
    content = sa.Column(sa.String, nullable=False)
    created_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now())
    post_id = sa.Column(sa.Integer, sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_id = sa.Column(sa.Integer, sa.ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    
    post = so.relationship("Posts")
    user = so.relationship("User")
    replies = so.relationship("Comment", remote_side=[id])
    updated_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=True)

class CommentVote(Base):
    __tablename__ = "comment_votes"
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    comment_id = sa.Column(sa.Integer, sa.ForeignKey("comments.id", ondelete="CASCADE"), primary_key=True)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = sa.Column(sa.Integer, primary_key=True, nullable=False)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_key = sa.Column(sa.String, nullable=False, unique=True)
    is_revoked = sa.Column(sa.Boolean, server_default='False', nullable=False)
    expires_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False)
    created_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now())


class Friendship(Base):
    __tablename__ = "friendships"

    id = sa.Column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requestor_id = sa.Column(sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    requested_id = sa.Column(sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = sa.Column(sa.Enum("pending", "accepted", "rejected", "blocked", name="friendship_status"), nullable=False, server_default="pending")
    created_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now())
    updated_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=True, onupdate=sa.func.now())

    __table_args__ = (
        sa.UniqueConstraint('requestor_id', 'requested_id', name='uq_friendships_requestor_requested'),
    )


class MediaFile(Base):
    __tablename__ = "media_files"

    id = sa.Column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    storage_key = sa.Column(sa.String, nullable=False, unique=True)
    url = sa.Column(sa.String, nullable=False)
    uploaded_by = sa.Column(sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now())

    uploader = so.relationship("User", foreign_keys=[uploaded_by])


class PostMedia(Base):
    __tablename__ = "post_media"

    id = sa.Column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = sa.Column(sa.Integer, sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    media_id = sa.Column(sa.UUID(as_uuid=True), sa.ForeignKey("media_files.id", ondelete="CASCADE"), nullable=False)
    order = sa.Column(sa.Integer, nullable=False, default=0)
    uploaded_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now())

    post = so.relationship("Posts", back_populates="media_attachments")
    media_file = so.relationship("MediaFile")


class RecoveryToken(Base):
    __tablename__ = "recovery_tokens"

    id = sa.Column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = sa.Column(sa.String, nullable=False, unique=True, index=True)
    exp_time = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False)
    revoked = sa.Column(sa.Boolean, server_default='False', nullable=False)
    date_issued = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now())

    user = so.relationship("User")

