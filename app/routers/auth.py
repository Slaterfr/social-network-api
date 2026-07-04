from fastapi import APIRouter, Depends, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import schemas, models
from app.repository.database import get_db
from app.dependencies.auth import get_current_user
from ..services import AuthService

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
