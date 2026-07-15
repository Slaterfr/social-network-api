"""Comment repository for comment-specific database queries."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app import models
from .base import BaseCRUD


class CommentRepository(BaseCRUD[models.Comment]):
    """Comment repository with specialized queries."""
    
    def __init__(self):
        super().__init__(models.Comment)
    
    def find_by_post(
        self, db: Session, post_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.Comment]:
        """Find all comments for a post."""
        return db.query(self.model).filter(
            self.model.post_id == post_id
        ).offset(skip).limit(limit).all()
    
    def find_by_user(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.Comment]:
        """Find all comments by a user."""
        return db.query(self.model).filter(
            self.model.user_id == user_id
        ).offset(skip).limit(limit).all()
    
    def find_top_level_comments(
        self, db: Session, post_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.Comment]:
        """Find top-level comments (no parent) for a post."""
        return db.query(self.model).filter(
            (self.model.post_id == post_id) & (self.model.parent_id == None)
        ).offset(skip).limit(limit).all()
    
    def find_replies(
        self, db: Session, parent_comment_id: int
    ) -> List[models.Comment]:
        """Find all replies to a comment."""
        return db.query(self.model).filter(
            self.model.parent_id == parent_comment_id
        ).all()
    
    def find_comment_thread(
        self, db: Session, comment_id: int
    ) -> Optional[models.Comment]:
        """Find a comment with all its replies (nested)."""
        comment = self.read(db, comment_id)
        if comment:
            comment.replies = self.find_replies(db, comment_id)
        return comment
    
    def find_recent_comments(
        self, db: Session, post_id: int, limit: int = 20
    ) -> List[models.Comment]:
        """Find recent comments for a post ordered by creation date."""
        return db.query(self.model).filter(
            self.model.post_id == post_id
        ).order_by(desc(self.model.created_at)).limit(limit).all()
    
    def user_is_owner(self, db: Session, comment_id: int, user_id: int) -> bool:
        """Check if a user is the owner of a comment."""
        comment = self.read(db, comment_id)
        return comment is not None and comment.user_id == user_id
    
    def find_by_post_and_user(
        self, db: Session, post_id: int, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.Comment]:
        """Find comments by user on a specific post."""
        return db.query(self.model).filter(
            (self.model.post_id == post_id) & (self.model.user_id == user_id)
        ).offset(skip).limit(limit).all()

    def _get_comments_with_stats_query(self, db: Session, current_user_id: Optional[int] = None):
        from sqlalchemy import func, literal
        
        vote_count_sub = db.query(func.count(models.CommentVote.user_id)).filter(
            models.CommentVote.comment_id == self.model.id
        ).correlate(self.model).as_scalar()

        if current_user_id:
            user_voted_sub = db.query(models.CommentVote).filter(
                models.CommentVote.comment_id == self.model.id,
                models.CommentVote.user_id == current_user_id
            ).correlate(self.model).exists()
        else:
            user_voted_sub = literal(False)
            
        return db.query(
            self.model,
            vote_count_sub.label("vote_count"),
            user_voted_sub.label("user_voted")
        )

    def find_by_post_with_stats(
        self, db: Session, post_id: int, current_user_id: Optional[int] = None, skip: int = 0, limit: int = 100
    ) -> List[models.Comment]:
        query = self._get_comments_with_stats_query(db, current_user_id)
        results = query.filter(
            self.model.post_id == post_id
        ).offset(skip).limit(limit).all()
        
        comments = []
        for comment, vote_count, user_voted in results:
            comment.vote_count = vote_count
            comment.user_voted = user_voted
            comments.append(comment)
        return comments

    def find_replies_with_stats(
        self, db: Session, parent_comment_id: int, current_user_id: Optional[int] = None
    ) -> List[models.Comment]:
        query = self._get_comments_with_stats_query(db, current_user_id)
        results = query.filter(
            self.model.parent_id == parent_comment_id
        ).all()
        
        comments = []
        for comment, vote_count, user_voted in results:
            comment.vote_count = vote_count
            comment.user_voted = user_voted
            comments.append(comment)
        return comments

    def find_by_id_stats(
        self, db: Session, comment_id: int, current_user_id: Optional[int] = None
    ) -> Optional[models.Comment]:
        query = self._get_comments_with_stats_query(db, current_user_id)
        result = query.filter(self.model.id == comment_id).first()
        if result:
            comment, vote_count, user_voted = result
            comment.vote_count = vote_count
            comment.user_voted = user_voted
            return comment
        return None
