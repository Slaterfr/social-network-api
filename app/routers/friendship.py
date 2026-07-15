from fastapi import Response, status, Depends, APIRouter
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from .. import schemas, models
from app.repository.database import get_db
from app.dependencies.auth import get_current_user
from ..services import FriendshipService

router = APIRouter(
    prefix="/friendships",
    tags=['Friendships']
)

friendship_service = FriendshipService()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.FriendshipResponse)
def request_friendship(
    request: schemas.FriendshipCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Send a friend request to another user.
    """
    return friendship_service.request_friendship(current_user.id, request.requested_id, db)


@router.put("/{friendship_id}/status", response_model=schemas.FriendshipResponse)
def update_friendship_status(
    friendship_id: UUID,
    status_update: schemas.FriendshipUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Update friendship status (accept, reject, or block a request).
    """
    return friendship_service.update_friendship_status(
        current_user.id, friendship_id, status_update.status, db
    )


@router.delete("/{friendship_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
def cancel_friend_request(
    friendship_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Cancel a pending friend request sent by current user.
    """
    friendship_service.cancel_friend_request(current_user.id, friendship_id, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{friendship_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_friendship(
    friendship_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Remove an accepted friendship.
    """
    friendship_service.remove_friendship(current_user.id, friendship_id, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/friends", response_model=List[schemas.FriendshipResponse])
def get_friends(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get current user's active friends list.
    """
    return friendship_service.get_friends_list(current_user.id, db, skip, limit)


@router.get("/requests/sent", response_model=List[schemas.FriendshipResponse])
def get_sent_requests(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get friend requests sent by current user.
    """
    return friendship_service.get_pending_sent(current_user.id, db, skip, limit)


@router.get("/requests/received", response_model=List[schemas.FriendshipResponse])
def get_received_requests(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get friend requests received by current user.
    """
    return friendship_service.get_pending_received(current_user.id, db, skip, limit)


@router.post("/block/{target_user_id}", response_model=schemas.FriendshipResponse)
def block_user(
    target_user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Block another user directly.
    """
    return friendship_service.block_user_explicit(current_user.id, target_user_id, db)


@router.get("/status/{target_user_id}", response_model=Optional[schemas.FriendshipResponse])
def get_friendship_status(
    target_user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get friendship status between current user and target user.
    """
    return friendship_service.get_friendship_status_bidirectional(current_user.id, target_user_id, db)


@router.get("/friends/{user_id}/profiles", response_model=List[schemas.UserPublicProfile])
def get_user_friends_profiles(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get active friends list of a specific user as profiles.
    """
    return friendship_service.get_friends_profiles(user_id, db, skip, limit)
