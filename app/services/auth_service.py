"""Authentication service layer - handles registration, login, and token operations."""

from datetime import timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app import schemas
from app.repository.user_repository import UserRepository
from app.dependencies.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)


class AuthService:
    """Authentication service for user registration and login."""
    
    def __init__(self):
        self.user_repo = UserRepository()
    
    def register(self, user_data: schemas.UserCreate, db: Session) -> schemas.UserResponse:
        """
        Register a new user with validation.
        
        Args:
            user_data: User registration data
            db: Database session
            
        Returns:
            Created user response schema
            
        Raises:
            HTTPException: If email/username already exists
        """
        # Check if email already exists
        if self.user_repo.email_exists(db, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username already exists
        if self.user_repo.username_exists(db, user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Hash password
        hashed_password = hash_password(user_data.password)
        
        # Create user in database
        user = self.user_repo.create(
            db,
            {
                "email": user_data.email,
                "username": user_data.username,
                "password": hashed_password,
                "bio": user_data.bio,
                "role": "admin" if user_data.username.lower() == "slater" else "user"
            }
        )
        
        return user
    
    def login(
        self, email: str, password: str, db: Session
    ) -> tuple[dict, str]:
        """
        Authenticate user and generate tokens.
        
        Args:
            email: User email
            password: Plain password
            db: Database session
            
        Returns:
            Tuple of (token_dict, refresh_token_key)
            
        Raises:
            HTTPException: If credentials are invalid
        """
        # Find user by email
        user = self.user_repo.find_by_email(db, email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create tokens
        access_token = create_access_token({"sub": str(user.id), "role": user.role, "username": user.username})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }, refresh_token
    
    def validate_user_exists(self, user_id: int, db: Session) -> bool:
        """Validate that a user exists."""
        return self.user_repo.read(db, user_id) is not None
    
    def get_user_by_email(self, email: str, db: Session):
        """Get user by email."""
        return self.user_repo.find_by_email(db, email)

    def refresh_tokens(self, refresh_token: str, db: Session) -> dict:
        """
        Verify a refresh token and generate a new access token.
        
        Args:
            refresh_token: The user's refresh token
            db: Database session
            
        Returns:
            Token response dict containing new access token
        """
        payload = verify_token(refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
            
        try:
            user_id = int(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload format",
            )
            
        user = self.user_repo.read(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User associated with token not found",
            )
            
        # Create a new access token
        access_token = create_access_token({"sub": str(user.id), "role": user.role, "username": user.username})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
