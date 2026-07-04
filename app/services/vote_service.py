"""Vote service layer - handles post and comment voting."""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app import schemas, models
from app.repository.vote_repository import VoteRepository
from app.repository.comment_vote_repository import CommentVoteRepository
from app.repository.post_repository import PostRepository
from app.repository.comment_repository import CommentRepository


class VoteService:
    """Service for post voting operations."""
    
    def __init__(self):
        self.vote_repo = VoteRepository()
        self.post_repo = PostRepository()
    
    def add_vote(self, post_id: int, user_id: int, db: Session) -> dict:
        """
        Add a vote (like) to a post.
        
        Args:
            post_id: Post ID
            user_id: User ID voting
            db: Database session
            
        Returns:
            Vote result dict
            
        Raises:
            HTTPException: If post doesn't exist or user already voted
        """
        # Check post exists
        if not self.post_repo.read(db, post_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post with id {post_id} not found"
            )
        
        # Check if already voted
        if self.vote_repo.user_voted_on_post(db, post_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already voted on this post"
            )
        
        # Add vote
        self.vote_repo.create(
            db,
            {
                "post_id": post_id,
                "user_id": user_id
            }
        )
        
        return {"message": "Successfully voted on post"}
    
    def remove_vote(self, post_id: int, user_id: int, db: Session) -> dict:
        """
        Remove a vote (like) from a post.
        
        Args:
            post_id: Post ID
            user_id: User ID removing vote
            db: Database session
            
        Returns:
            Result dict
            
        Raises:
            HTTPException: If vote doesn't exist
        """
        vote = self.vote_repo.find_vote(db, post_id, user_id)
        
        if not vote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vote not found"
            )
        
        db.delete(vote)
        db.commit()
        
        return {"message": "Successfully removed vote from post"}
    
    def get_vote_count(self, post_id: int, db: Session) -> int:
        """Get total vote count for a post."""
        return self.vote_repo.get_vote_count(db, post_id)
    
    def user_voted(self, post_id: int, user_id: int, db: Session) -> bool:
        """Check if user voted on post."""
        return self.vote_repo.user_voted_on_post(db, post_id, user_id)


class CommentVoteService:
    """Service for comment voting operations."""
    
    def __init__(self):
        self.comment_vote_repo = CommentVoteRepository()
        self.comment_repo = CommentRepository()
    
    def add_comment_vote(self, comment_id: int, user_id: int, db: Session) -> dict:
        """
        Add a vote (like) to a comment.
        
        Args:
            comment_id: Comment ID
            user_id: User ID voting
            db: Database session
            
        Returns:
            Vote result dict
            
        Raises:
            HTTPException: If comment doesn't exist or user already voted
        """
        # Check comment exists
        if not self.comment_repo.read(db, comment_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment with id {comment_id} not found"
            )
        
        # Check if already voted
        if self.comment_vote_repo.user_voted_on_comment(db, comment_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already voted on this comment"
            )
        
        # Add vote
        self.comment_vote_repo.create(
            db,
            {
                "comment_id": comment_id,
                "user_id": user_id
            }
        )
        
        return {"message": "Successfully voted on comment"}
    
    def remove_comment_vote(self, comment_id: int, user_id: int, db: Session) -> dict:
        """
        Remove a vote from a comment.
        
        Args:
            comment_id: Comment ID
            user_id: User ID removing vote
            db: Database session
            
        Returns:
            Result dict
            
        Raises:
            HTTPException: If vote doesn't exist
        """
        vote = self.comment_vote_repo.find_comment_vote(db, comment_id, user_id)
        
        if not vote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vote not found"
            )
        
        db.delete(vote)
        db.commit()
        
        return {"message": "Successfully removed vote from comment"}
    
    def get_comment_vote_count(self, comment_id: int, db: Session) -> int:
        """Get total vote count for a comment."""
        return self.comment_vote_repo.get_comment_vote_count(db, comment_id)
    
    def user_voted(self, comment_id: int, user_id: int, db: Session) -> bool:
        """Check if user voted on comment."""
        return self.comment_vote_repo.user_voted_on_comment(db, comment_id, user_id)
