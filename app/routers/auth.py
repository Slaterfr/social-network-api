from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import secrets
import hashlib
from datetime import datetime, timedelta, timezone

from .. import schemas, models
from app.repository.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.security import hash_password
from ..services import AuthService
from app.services.email_service import MailService

router = APIRouter(
    prefix="/auth",
    tags=['Authentication']
)

auth_service = AuthService()


@router.post('/register', response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    - **email**: Valid email address (must be unique)
    - **username**: Username 3-50 characters (must be unique)
    - **password**: Password 8+ characters (requires uppercase and digit)
    - **bio**: Optional profile bio (max 500 characters)
    
    Returns the created user.
    """
    user = auth_service.register(user_data, db)
    return user


@router.post('/login', response_model=schemas.Token)
def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login user with email and password.
    
    - **username**: Email address
    - **password**: User password
    
    Returns access_token (30 min) and refresh_token (7 days).
    """
    token_dict, _ = auth_service.login(
        email=user_credentials.username,
        password=user_credentials.password,
        db=db
    )
    return token_dict


@router.post('/logout')
def logout(current_user: models.User = Depends(get_current_user)):
    """
    Logout user (frontend should discard tokens).
    
    Requires authentication.
    """
    return {"message": "Logged out successfully"}


@router.post('/refresh', response_model=schemas.Token)
def refresh(
    payload: schemas.RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using a valid refresh token.
    """
    token_dict = auth_service.refresh_tokens(
        refresh_token=payload.refresh_token,
        db=db
    )
    return token_dict


@router.post('/forgot-password')
def forgot_password(
    req: schemas.ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Initiate password recovery. Generates a secure token, hashes it,
    stores it in the database, and sends a recovery email with a reset link.
    """
    # 1. Check if user exists
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if not user:
        # For security, do not leak user existence (return generic success message)
        return {"message": "Recovery email sent if the address exists"}

    # 2. Generate raw token
    raw_token = secrets.token_urlsafe(32)

    # 3. Hash token
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    # 4. Save to db
    exp_time = datetime.now(timezone.utc) + timedelta(minutes=15)
    recovery_record = models.RecoveryToken(
        user_id=user.id,
        token_hash=token_hash,
        exp_time=exp_time,
        revoked=False
    )
    db.add(recovery_record)
    db.commit()

    # 5. Add email task to background
    background_tasks.add_task(
        MailService.send_password_recovery_email,
        user.email,
        raw_token,
        req.lang
    )

    return {"message": "Recovery email sent if the address exists"}


@router.post('/reset-password')
def reset_password(
    req: schemas.ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using a valid, unexpired, unrevoked recovery token.
    """
    # 1. Hash the incoming raw token
    token_hash = hashlib.sha256(req.token.encode()).hexdigest()

    # 2. Find in DB
    recovery_record = db.query(models.RecoveryToken).filter(
        models.RecoveryToken.token_hash == token_hash,
        models.RecoveryToken.revoked == False,
        models.RecoveryToken.exp_time > datetime.now(timezone.utc)
    ).first()

    if not recovery_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid, expired, or already used recovery token"
        )

    # 3. Retrieve user
    user = db.query(models.User).filter(models.User.id == recovery_record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 4. Hash new password and update user
    user.password = hash_password(req.new_password)

    # 5. Revoke token
    recovery_record.revoked = True

    # 6. Revoke user's refresh tokens (force logout everywhere for security)
    db.query(models.RefreshToken).filter(models.RefreshToken.user_id == user.id).update(
        {"is_revoked": True}
    )

    db.commit()

    return {"message": "Password reset successfully"}
