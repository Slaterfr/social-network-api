from fastapi import Response, status, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import schemas, models
from app.repository.database import get_db
from app.dependencies.auth import get_current_user, get_optional_user
from ..services import CommentService

router = APIRouter(
    prefix="/comments",
    tags=['Comments']
)

comment_service = CommentService()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.CommentResponse)
def create_comment(
    comment: schemas.CommentCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    return comment_service.create_comment(comment, current_user.id, db)


@router.get("/{post_id}", response_model=List[schemas.CommentResponse])
def get_comments(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user)
):
    return comment_service.get_post_comments(post_id, db, current_user)


@router.put("/{comment_id}", response_model=schemas.CommentResponse)
def update_comment(
    comment_id: int,
    updated_comment: schemas.CommentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return comment_service.update_comment(comment_id, current_user, updated_comment, db)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    comment_service.delete_comment(comment_id, current_user, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

