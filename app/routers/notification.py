"""Notification router layer."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, models
from app.repository.database import get_db
from app.dependencies.auth import get_current_user
from ..services import NotificationService

router = APIRouter(
    prefix="/notifications",
    tags=['Notifications']
)

notification_service = NotificationService()


@router.get("", response_model=schemas.NotificationListResponse)
def get_notifications(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get notifications for the current authenticated user.
    """
    return notification_service.get_notifications(
        current_user.id, db, skip, limit
    )
