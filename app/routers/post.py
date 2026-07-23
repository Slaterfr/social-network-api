from fastapi import Response, status, Depends, APIRouter, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from .. import schemas, models
from app.repository.database import get_db
from app.dependencies.auth import get_current_user
from ..services import PostService, FileManagementService

router = APIRouter(
    prefix='/posts',
    tags=['Posts']
)

post_service = PostService()
file_management_service = FileManagementService()


@router.get('/', response_model=list[schemas.PostResponse])
def get_posts(db: Session = Depends(get_db), limit: int = 10, skip: int = 0, search: Optional[str] = "", user_id: Optional[int] = None):
    if user_id is not None:
        return post_service.get_user_posts(user_id, db, skip, limit)
    return post_service.get_all_posts(db, skip, limit, search)


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.PostResponse)
def create_posts(post: schemas.PostCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if post.type == "announcement" and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create announcements"
        )
    return post_service.create_post(post, current_user.id, db)


@router.get('/announcements', response_model=list[schemas.PostResponse])
def get_announcements(db: Session = Depends(get_db)):
    return post_service.get_announcements(db, limit=3)


@router.get('/suggestions', response_model=list[schemas.PostResponse])
def get_suggestions(
    db: Session = Depends(get_db),
    sort_by: str = "votes",
    skip: int = 0,
    limit: int = 10,
    current_user: models.User = Depends(get_current_user)
):
    return post_service.get_suggestions(db, current_user, sort_by, skip, limit)


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


@router.post('/upload', status_code=status.HTTP_201_CREATED)
async def upload_post_media(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Upload a media file attachment for a new post.
    
    Verifies that the upload is a valid image and returns the database media UUID and preview URL.
    """
    media = await file_management_service.upload_file(file, "posts", current_user.id, db)
    preview_url = file_management_service.generate_url(media.storage_key)
    return {
        "id": media.id,
        "url": preview_url
    }