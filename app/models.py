from .database import Base
import sqlalchemy as sa

class Posts(Base):
    __tablename__ = "posts"

    id = sa.Column(sa.Integer, primary_key=True, nullable=False)
    title = sa.Column(sa.String, nullable=False)
    content = sa.Column(sa.String, nullable=False)
    published = sa.Column(sa.Boolean, server_default='True', nullable=False)
    created_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'))


class User(Base):
    __tablename__ = "users"
    id = sa.Column(sa.Integer, primary_key=True, nullable=False)
    email = sa.Column(sa.String, nullable=False, unique=True )
    password = sa.Column(sa.String, nullable=False, )
    created_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'))





    