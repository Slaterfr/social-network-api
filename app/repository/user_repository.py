"""User repository for user-specific database queries."""

from typing import Optional
from sqlalchemy.orm import Session

from app import models
from .base import BaseCRUD


class UserRepository(BaseCRUD[models.User]):
    """User repository with specialized queries."""
    
    def __init__(self):
        super().__init__(models.User)
    
    def find_by_email(self, db: Session, email: str) -> Optional[models.User]:
        """Find user by email address."""
        return db.query(self.model).filter(self.model.email == email).first()
    
    def find_by_username(self, db: Session, username: str) -> Optional[models.User]:
        """Find user by username."""
        return db.query(self.model).filter(self.model.username == username).first()
    
    def find_by_email_or_username(
        self, db: Session, email_or_username: str
    ) -> Optional[models.User]:
        """Find user by either email or username."""
        return db.query(self.model).filter(
            (self.model.email == email_or_username) | 
            (self.model.username == email_or_username)
        ).first()
    
    def email_exists(self, db: Session, email: str) -> bool:
        """Check if email exists in database."""
        return db.query(self.model).filter(self.model.email == email).first() is not None
    
    def username_exists(self, db: Session, username: str) -> bool:
        """Check if username exists in database."""
        return db.query(self.model).filter(self.model.username == username).first() is not None
    
    def find_by_role(self, db: Session, role: str, skip: int = 0, limit: int = 100):
        """Find users by role with pagination."""
        return db.query(self.model).filter(
            self.model.role == role
        ).offset(skip).limit(limit).all()
