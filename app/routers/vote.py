from typing import Optional
from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import schemas, models
from app.repository.database import get_db
from app.dependencies.auth import get_current_user, get_optional_user
from ..services import VoteService, CommentVoteService

router = APIRouter(
    prefix="/vote",
    tags=['Vote']
)

vote_service = VoteService()
comment_vote_service = CommentVoteService()


# Get Post Vote Stats
@router.get("/post/{post_id}", response_model=schemas.VoteStats)
def get_post_vote_stats(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user)
):
    """
    Get total votes count for a post and whether the current user voted on it.
    """
    vote_count = vote_service.get_vote_count(post_id, db)
    user_voted = False
    if current_user:
        user_voted = vote_service.user_voted(post_id, current_user.id, db)
        
    return {
        "post_id": post_id,
        "vote_count": vote_count,
        "user_voted": user_voted
    }


# Get Comment Vote Stats
@router.get("/comment/{comment_id}", response_model=schemas.CommentVoteStats)
def get_comment_vote_stats(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user)
):
    """
    Get total votes count for a comment and whether the current user voted on it.
    """
    vote_count = comment_vote_service.get_comment_vote_count(comment_id, db)
    user_voted = False
    if current_user:
        user_voted = comment_vote_service.user_voted(comment_id, current_user.id, db)
        
    return {
        "comment_id": comment_id,
        "vote_count": vote_count,
        "user_voted": user_voted
    }



# Post Vote
@router.post("/", status_code=status.HTTP_201_CREATED)
def vote_post(
    vote: schemas.VoteCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Vote/Like a post. If already voted, it will unlike/remove the vote (toggle behavior).
    """
    if vote_service.user_voted(vote.post_id, current_user.id, db):
        return vote_service.remove_vote(vote.post_id, current_user.id, db)
    else:
        return vote_service.add_vote(vote.post_id, current_user.id, db)


# Comment Vote
@router.post("/comment", status_code=status.HTTP_201_CREATED)
def vote_comment(
    vote: schemas.CommentVoteCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Vote/Like a comment. If already voted, it will unlike/remove the vote (toggle behavior).
    """
    if comment_vote_service.user_voted(vote.comment_id, current_user.id, db):
        return comment_vote_service.remove_comment_vote(vote.comment_id, current_user.id, db)
    else:
        return comment_vote_service.add_comment_vote(vote.comment_id, current_user.id, db)

