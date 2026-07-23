"""Post repository for post-specific database queries."""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

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
        ).order_by(desc(self.model.created_at)).offset(skip).limit(limit).all()
    
    def find_published(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[models.Posts]:
        """Find all published posts."""
        return db.query(self.model).filter(
            self.model.published == True
        ).order_by(desc(self.model.created_at)).offset(skip).limit(limit).all()
    
    def find_by_owner_published(
        self, db: Session, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.Posts]:
        """Find published posts by owner."""
        return db.query(self.model).filter(
            (self.model.owner_id == owner_id) & (self.model.published == True)
        ).order_by(desc(self.model.created_at)).offset(skip).limit(limit).all()
    
    def find_with_search(
        self, db: Session, search: str = "", skip: int = 0, limit: int = 100
    ) -> List[models.Posts]:
        """Find posts by title or content containing search term."""
        return db.query(self.model).filter(
            or_(self.model.title.contains(search), self.model.content.contains(search))
        ).order_by(desc(self.model.created_at)).offset(skip).limit(limit).all()
    
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

    def _get_posts_with_stats_query(self, db: Session, current_user_id: Optional[int] = None):
        from sqlalchemy import func, literal
        
        vote_count_sub = db.query(func.count(models.Vote.user_id)).filter(
            models.Vote.post_id == self.model.id
        ).correlate(self.model).as_scalar()

        comment_count_sub = db.query(func.count(models.Comment.id)).filter(
            models.Comment.post_id == self.model.id
        ).correlate(self.model).as_scalar()

        if current_user_id:
            user_voted_sub = db.query(models.Vote).filter(
                models.Vote.post_id == self.model.id,
                models.Vote.user_id == current_user_id
            ).correlate(self.model).exists()
        else:
            user_voted_sub = literal(False)
            
        return db.query(
            self.model,
            vote_count_sub.label("vote_count"),
            comment_count_sub.label("comment_count"),
            user_voted_sub.label("user_voted")
        )

    def find_published_stats(
        self, db: Session, current_user_id: Optional[int] = None, skip: int = 0, limit: int = 100
    ) -> List[models.Posts]:
        query = self._get_posts_with_stats_query(db, current_user_id)
        results = query.filter(
            self.model.published == True,
            self.model.type == "post"
        ).order_by(desc(self.model.created_at)).offset(skip).limit(limit).all()
        
        posts = []
        for post, vote_count, comment_count, user_voted in results:
            post.vote_count = vote_count
            post.comment_count = comment_count
            post.user_voted = user_voted
            posts.append(post)
        return posts

    def find_by_owner_stats(
        self, db: Session, owner_id: int, current_user_id: Optional[int] = None, skip: int = 0, limit: int = 100
    ) -> List[models.Posts]:
        query = self._get_posts_with_stats_query(db, current_user_id)
        results = query.filter(
            self.model.owner_id == owner_id,
            self.model.type == "post"
        ).order_by(desc(self.model.created_at)).offset(skip).limit(limit).all()
        
        posts = []
        for post, vote_count, comment_count, user_voted in results:
            post.vote_count = vote_count
            post.comment_count = comment_count
            post.user_voted = user_voted
            posts.append(post)
        return posts

    def find_with_search_stats(
        self, db: Session, search: str, current_user_id: Optional[int] = None, skip: int = 0, limit: int = 100
    ) -> List[models.Posts]:
        query = self._get_posts_with_stats_query(db, current_user_id)
        results = query.filter(
            or_(self.model.title.contains(search), self.model.content.contains(search)),
            self.model.type == "post"
        ).order_by(desc(self.model.created_at)).offset(skip).limit(limit).all()
        
        posts = []
        for post, vote_count, comment_count, user_voted in results:
            post.vote_count = vote_count
            post.comment_count = comment_count
            post.user_voted = user_voted
            posts.append(post)
        return posts

    def find_announcements_stats(
        self, db: Session, limit: int = 3
    ) -> List[models.Posts]:
        query = self._get_posts_with_stats_query(db, None)
        results = query.filter(
            self.model.published == True,
            self.model.type == "announcement"
        ).order_by(desc(self.model.created_at)).limit(limit).all()
        
        posts = []
        for post, vote_count, comment_count, user_voted in results:
            post.vote_count = vote_count
            post.comment_count = comment_count
            post.user_voted = user_voted
            posts.append(post)
        return posts

    def find_suggestions_stats(
        self, db: Session, current_user_id: Optional[int] = None, sort_by: str = "votes", skip: int = 0, limit: int = 100
    ) -> List[models.Posts]:
        from sqlalchemy import text
        query = self._get_posts_with_stats_query(db, current_user_id)
        query = query.filter(
            self.model.published == True,
            self.model.type == "suggestion"
        )
        if sort_by == "votes":
            query = query.order_by(desc(text("vote_count")), desc(self.model.created_at))
        else:
            query = query.order_by(desc(self.model.created_at))
            
        results = query.offset(skip).limit(limit).all()
        posts = []
        for post, vote_count, comment_count, user_voted in results:
            post.vote_count = vote_count
            post.comment_count = comment_count
            post.user_voted = user_voted
            posts.append(post)
        return posts

    def find_by_id_stats(
        self, db: Session, post_id: int, current_user_id: Optional[int] = None
    ) -> Optional[models.Posts]:
        query = self._get_posts_with_stats_query(db, current_user_id)
        result = query.filter(self.model.id == post_id).first()
        if result:
            post, vote_count, comment_count, user_voted = result
            post.vote_count = vote_count
            post.comment_count = comment_count
            post.user_voted = user_voted
            return post
        return None
