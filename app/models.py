from .database import Base
import sqlalchemy as sa
import sqlalchemy.orm as so


class Posts(Base):
    __tablename__ = "posts"

    id = sa.Column(sa.Integer, primary_key=True, nullable=False)
    title = sa.Column(sa.String, nullable=False)
    content = sa.Column(sa.String, nullable=False)
    published = sa.Column(sa.Boolean, server_default='True', nullable=False)
    created_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'))
    owner_id = sa.Column(sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner = so.relationship("User")
    number = sa.Column(sa.String, )

class User(Base):
    __tablename__ = "users"
    id = sa.Column(sa.Integer, primary_key=True, nullable=False)
    email = sa.Column(sa.String, nullable=False, unique=True )
    password = sa.Column(sa.String, nullable=False, )
    created_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'))

    
class Vote(Base):
    __tablename__ = "votes"
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    post_id = sa.Column(sa.Integer, sa.ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    




    