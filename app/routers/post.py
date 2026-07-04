from fastapi import Response, status, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import Optional

from .. import schemas, models
from app.repository.database import get_db
from app.dependencies.auth import get_current_user
from ..services import PostService

router = APIRouter(
    prefix='/posts',
    tags=['Posts']
)

post_service = PostService()


@router.get('/', response_model=list[schemas.PostResponse])
def get_posts(db: Session = Depends(get_db), limit: int = 10, skip: int = 0, search: Optional[str] = ""):
    return post_service.get_all_posts(db, skip, limit, search)


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.PostResponse)
def create_posts(post: schemas.PostCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return post_service.create_post(post, current_user.id, db)


@router.get('/{id}', response_model=schemas.PostResponse)
def get_post(id: int, db: Session = Depends(get_db)):
    return post_service.get_post(id, db)


@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    post_service.delete_post(id, current_user, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put('/{id}', response_model=schemas.PostResponse)
def update_post(id: int, updated_post: schemas.PostUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return post_service.update_post(id, current_user, updated_post, db)