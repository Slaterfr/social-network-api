"""Post service layer - handles post CRUD operations with authorization."""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app import schemas, models
from app.repository.post_repository import PostRepository
from app.repository.vote_repository import VoteRepository
from .file_management import FileManagementService


class PostService:
    """Post service for CRUD operations and authorization."""
    
    def __init__(self):
        self.post_repo = PostRepository()
        self.vote_repo = VoteRepository()
        self.file_management = FileManagementService()
    
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
        initial_status = None
        if post_data.type == "suggestion":
            initial_status = "under_review"

        post = self.post_repo.create(
            db,
            {
                "title": post_data.title,
                "content": post_data.content,
                "published": post_data.published,
                "owner_id": owner_id,
                "type": post_data.type,
                "status": initial_status
            }
        )
        
        # Link media attachments if provided
        if post_data.media_ids:
            for idx, media_id in enumerate(post_data.media_ids):
                db.add(models.PostMedia(
                    post_id=post.id,
                    media_id=media_id,
                    order=idx
                ))
            db.commit()
            db.refresh(post)

        return self._attach_post_media_urls(post, db)
    
    def get_post(self, post_id: int, db: Session, current_user: Optional[models.User] = None) -> models.Posts:
        """
        Get post by ID.
        
        Args:
            post_id: Post ID
            db: Database session
            current_user: Optional current logged in user
            
        Returns:
            Post model
            
        Raises:
            HTTPException: If post not found
        """
        current_user_id = current_user.id if current_user else None
        post = self.post_repo.find_by_id_stats(db, post_id, current_user_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post with id {post_id} not found"
            )
        return self._attach_post_media_urls(post, db)
    
    def get_all_posts(
        self, db: Session, skip: int = 0, limit: int = 10, search: str = "", current_user: Optional[models.User] = None
    ) -> List[models.Posts]:
        """
        Get all posts with optional search.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Max records to return
            search: Search term for title
            current_user: Optional current logged in user
            
        Returns:
            List of posts
        """
        current_user_id = current_user.id if current_user else None
        if search:
            posts = self.post_repo.find_with_search_stats(db, search, current_user_id, skip, limit)
        else:
            posts = self.post_repo.find_published_stats(db, current_user_id, skip, limit)
        return [self._attach_post_media_urls(p, db) for p in posts]
    
    def get_user_posts(
        self, user_id: int, db: Session, skip: int = 0, limit: int = 10, current_user: Optional[models.User] = None
    ) -> List[models.Posts]:
        """
        Get all posts by a user.
        
        Args:
            user_id: User ID
            db: Database session
            skip: Number of records to skip
            limit: Max records to return
            current_user: Optional current logged in user
            
        Returns:
            List of user's posts
        """
        current_user_id = current_user.id if current_user else None
        posts = self.post_repo.find_by_owner_stats(db, user_id, current_user_id, skip, limit)
        return [self._attach_post_media_urls(p, db) for p in posts]
    
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
        post = self.get_post(post_id, db, current_user)
        
        # Check authorization: owner or admin
        if post.owner_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this post"
            )
        
        data_to_update = update_data.dict(exclude_unset=True)
        
        if "status" in data_to_update and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can update the status of suggestions"
            )

        data_to_update["updated_at"] = datetime.now(timezone.utc)
        
        updated_post = self.post_repo.update(
            db, post_id, data_to_update
        )
        post_with_stats = self.post_repo.find_by_id_stats(db, post_id, current_user.id)
        return self._attach_post_media_urls(post_with_stats, db)
    
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

    def _attach_post_media_urls(self, post: models.Posts, db: Session) -> models.Posts:
        """Attach presigned avatar and attachment download URLs to a post."""
        if not post:
            return post

        # 1. Attach post owner's avatar URL
        if post.owner:
            if post.owner.avatar:
                try:
                    post.owner.avatar_url = self.file_management.generate_url(post.owner.avatar.storage_key)
                except Exception:
                    post.owner.avatar_url = None
            else:
                post.owner.avatar_url = None

        # 2. Attach post's attachment media URLs
        urls = []
        if post.media_attachments:
            for attachment in post.media_attachments:
                if attachment.media_file:
                    try:
                        url = self.file_management.generate_url(attachment.media_file.storage_key)
                        urls.append(url)
                    except Exception:
                        pass
        post.media_urls = urls

        # Ensure properties exist
        if not hasattr(post, 'comment_count'):
            post.comment_count = 0
        if not hasattr(post, 'vote_count'):
            post.vote_count = 0
        if not hasattr(post, 'user_voted'):
            post.user_voted = False

        return post
    
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

    def get_announcements(self, db: Session, limit: int = 3) -> List[models.Posts]:
        """Get latest announcements."""
        posts = self.post_repo.find_announcements_stats(db, limit)
        return [self._attach_post_media_urls(p, db) for p in posts]

    def get_suggestions(
        self, db: Session, current_user: Optional[models.User] = None, sort_by: str = "votes", skip: int = 0, limit: int = 10
    ) -> List[models.Posts]:
        """Get suggestions."""
        current_user_id = current_user.id if current_user else None
        posts = self.post_repo.find_suggestions_stats(db, current_user_id, sort_by, skip, limit)
        return [self._attach_post_media_urls(p, db) for p in posts]
