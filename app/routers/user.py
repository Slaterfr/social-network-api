from fastapi import APIRouter, Depends, status, HTTPException, File, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session

from .. import schemas, models
from app.repository.database import get_db
from app.dependencies.auth import get_current_user
from ..services import UserService, AuthService
from app.services.email_service import MailService

router = APIRouter(
    prefix='/users',
    tags=['Users']
)

user_service = UserService()
auth_service = AuthService()


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
def create_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account (alternative to /auth/register).
    
    - **email**: Valid email address (must be unique)
    - **username**: Username 3-50 characters (must be unique)
    - **password**: Password 8+ characters (requires uppercase and digit)
    - **bio**: Optional profile bio (max 500 characters)
    
    Returns the created user.
    """
    user = auth_service.register(user_data, db)
    return user


@router.get('/me', response_model=schemas.UserResponse)
def get_current_user_profile(current_user: models.User = Depends(get_current_user)):
    """
    Get current authenticated user's profile.
    
    Requires authentication token.
    """
    return user_service.attach_avatar_url(current_user)


@router.post('/me/avatar', response_model=schemas.UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Upload a new profile picture (avatar) for the current user.
    
    Checks that the file is a valid image and converts it to WebP before uploading to S3.
    """
    updated_user = await user_service.update_avatar(current_user, file, db)
    return updated_user


@router.get('/{user_id}', response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get user profile by ID.
    
    Returns basic user information (email, username, bio, role).
    """
    user = user_service.get_user(user_id, db)
    return user


@router.get('/profile/{username}', response_model=list[schemas.UserPublicProfile])
def get_user_by_username(username: str, db: Session = Depends(get_db)):
    """
    Get public user profiles matching username pattern (case-insensitive LIKE search).
    """
    users = user_service.get_user_by_username(username, db)
    return users


@router.put('/me', response_model=schemas.UserResponse)
def update_current_user_profile(
    update_data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Update current user's profile.
    
    Requires authentication token.
    Can update: username, bio
    """
    updated_user = user_service.update_profile(current_user.id, update_data, db)
    return updated_user


@router.post('/me/change-password')
def change_password(
    change_pwd: schemas.UserChangePassword,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Change current user's password.
    
    Requires authentication token and old password verification.
    """
    user_service.change_password(
        current_user.id,
        change_pwd.old_password,
        change_pwd.new_password,
        db
    )
    return {"message": "Password changed successfully"}


def send_bulk_announcements_task(subject: str, body: str, db: Session):
    # Fetch all active users who have emails
    users = db.query(models.User).all()
    for u in users:
        if u.email:
            try:
                MailService.send_announcement_email(u.email, subject, body)
            except Exception as e:
                print(f"Failed to send broadcast email to {u.email}: {e}")


@router.post('/admin/broadcast-email', status_code=status.HTTP_200_OK)
def broadcast_admin_email(
    broadcast_data: schemas.AdminEmailBroadcast,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Broadcast an email message to all registered users.
    Only administrators are authorized to perform this operation.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can send system broadcasts"
        )
    
    if broadcast_data.test_email:
        try:
            MailService.send_announcement_email(
                str(broadcast_data.test_email), 
                broadcast_data.subject, 
                broadcast_data.body
            )
            return {"message": f"Test email sent to {broadcast_data.test_email}"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send test email: {str(e)}"
            )

    background_tasks.add_task(
        send_bulk_announcements_task, 
        broadcast_data.subject, 
        broadcast_data.body, 
        db
    )
    return {"message": "Email broadcast successfully queued in the background"}
