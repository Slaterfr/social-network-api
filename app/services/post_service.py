"""Post service layer - handles post CRUD operations with authorization."""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app import schemas, models
from app.repository.post_repository import PostRepository
from app.repository.vote_repository import VoteRepository


class PostService:
    """Post service for CRUD operations and authorization."""
    
    def __init__(self):
        self.post_repo = PostRepository()
        self.vote_repo = VoteRepository()
    
    def create_post(
        self, post_data: schemas.PostCreate, owner_id: int, db: Session
    ) -> models.Posts:
        """
        Create a new post.
        
        Args:
            post_data: Post data
            owner_id: ID of post owner (current user)
            db: Database session
            
        Returns:
            Created post model
        """
        post = self.post_repo.create(
            db,
            {
                "title": post_data.title,
                "content": post_data.content,
                "published": post_data.published,
                "owner_id": owner_id
            }
        )
        return post
    
    def get_post(self, post_id: int, db: Session) -> models.Posts:
        """
        Get post by ID.
        
        Args:
            post_id: Post ID
            db: Database session
            
        Returns:
            Post model
            
        Raises:
            HTTPException: If post not found
        """
        post = self.post_repo.read(db, post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post with id {post_id} not found"
            )
        return post
    
    def get_all_posts(
        self, db: Session, skip: int = 0, limit: int = 10, search: str = ""
    ) -> List[models.Posts]:
        """
        Get all posts with optional search.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Max records to return
            search: Search term for title
            
        Returns:
            List of posts
        """
        if search:
            return self.post_repo.find_with_search(db, search, skip, limit)
        return self.post_repo.find_published(db, skip, limit)
    
    def get_user_posts(
        self, user_id: int, db: Session, skip: int = 0, limit: int = 10
    ) -> List[models.Posts]:
        """
        Get all posts by a user.
        
        Args:
            user_id: User ID
            db: Database session
            skip: Number of records to skip
            limit: Max records to return
            
        Returns:
            List of user's posts
        """
        return self.post_repo.find_by_owner(db, user_id, skip, limit)
    
    def update_post(
        self, post_id: int, current_user: models.User, update_data: schemas.PostUpdate, db: Session
    ) -> models.Posts:
        """
        Update post with authorization check.
        
        Args:
            post_id: Post ID
            current_user: User object making request (authorization)
            update_data: Data to update
            db: Database session
            
        Returns:
            Updated post model
            
        Raises:
            HTTPException: If post not found or user not authorized
        """
        post = self.get_post(post_id, db)
        
        # Check authorization: owner or admin
        if post.owner_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this post"
            )
        
        data_to_update = update_data.dict(exclude_unset=True)
        data_to_update["updated_at"] = datetime.now(timezone.utc)
        
        updated_post = self.post_repo.update(
            db, post_id, data_to_update
        )
        return updated_post
    
    def delete_post(self, post_id: int, current_user: models.User, db: Session) -> bool:
        """
        Delete post with authorization check.
        
        Args:
            post_id: Post ID
            current_user: User object making request (authorization)
            db: Database session
            
        Returns:
            True if deleted
            
        Raises:
            HTTPException: If post not found or user not authorized
        """
        post = self.get_post(post_id, db)
        
        # Check authorization: owner or admin
        if post.owner_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this post"
            )
        
        return self.post_repo.delete(db, post_id)
    
    def get_post_with_stats(self, post_id: int, db: Session) -> dict:
        """
        Get post with vote and comment counts.
        
        Args:
            post_id: Post ID
            db: Database session
            
        Returns:
            Post dict with stats
        """
        post = self.get_post(post_id, db)
        vote_count = self.vote_repo.get_vote_count(db, post_id)
        
        return {
            "post": post,
            "vote_count": vote_count
        }
    
    def post_exists(self, post_id: int, db: Session) -> bool:
        """Check if post exists."""
        return self.post_repo.read(db, post_id) is not None
