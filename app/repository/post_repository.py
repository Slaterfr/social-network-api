"""Post repository for post-specific database queries."""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app import models
from .base import BaseCRUD


class PostRepository(BaseCRUD[models.Posts]):
    """Post repository with specialized queries."""
    
    def __init__(self):
        super().__init__(models.Posts)
    
    def find_by_owner(
        self, db: Session, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.Posts]:
        """Find all posts by owner (user)."""
        return db.query(self.model).filter(
            self.model.owner_id == owner_id
        ).offset(skip).limit(limit).all()
    
    def find_published(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[models.Posts]:
        """Find all published posts."""
        return db.query(self.model).filter(
            self.model.published == True
        ).offset(skip).limit(limit).all()
    
    def find_by_owner_published(
        self, db: Session, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.Posts]:
        """Find published posts by owner."""
        return db.query(self.model).filter(
            (self.model.owner_id == owner_id) & (self.model.published == True)
        ).offset(skip).limit(limit).all()
    
    def find_with_search(
        self, db: Session, search: str = "", skip: int = 0, limit: int = 100
    ) -> List[models.Posts]:
        """Find posts by title containing search term."""
        return db.query(self.model).filter(
            self.model.title.contains(search)
        ).offset(skip).limit(limit).all()
    
    def find_recent(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[models.Posts]:
        """Find recent posts ordered by creation date (newest first)."""
        return db.query(self.model).order_by(
            desc(self.model.created_at)
        ).offset(skip).limit(limit).all()
    
    def find_with_vote_count(
        self, db: Session, post_id: int
    ):
        """Find post with vote count (likes)."""
        from sqlalchemy import func
        
        post = db.query(self.model).filter(self.model.id == post_id).first()
        if post:
            vote_count = db.query(func.count(models.Vote.user_id)).filter(
                models.Vote.post_id == post_id
            ).scalar()
            return post, vote_count
        return None, 0
    
    def find_with_comment_count(
        self, db: Session, post_id: int
    ):
        """Find post with comment count."""
        from sqlalchemy import func
        
        post = db.query(self.model).filter(self.model.id == post_id).first()
        if post:
            comment_count = db.query(func.count(models.Comment.id)).filter(
                models.Comment.post_id == post_id
            ).scalar()
            return post, comment_count
        return None, 0
    
    def owner_is(self, db: Session, post_id: int, user_id: int) -> bool:
        """Check if a user is the owner of a post."""
        post = self.read(db, post_id)
        return post is not None and post.owner_id == user_id
