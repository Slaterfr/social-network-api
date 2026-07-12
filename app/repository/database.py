"""Database configuration and session management in the repository layer."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

from app.core.config import Config

# Create database engine
engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URL,
    connect_args={
        "client_encoding": "utf8"
    } if "postgresql" in (Config.SQLALCHEMY_DATABASE_URL or "") else {
        "check_same_thread": False
    } if "sqlite" in (Config.SQLALCHEMY_DATABASE_URL or "") else {},
    pool_pre_ping=True,
    pool_recycle=1800
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model class
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency for getting database session.
    Automatically closes session after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
