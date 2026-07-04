"""Friendship service layer - handles friendship business logic and CRUD operations."""

from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from app import schemas, models
from app.repository.friendship_repository import FriendshipRepository
from app.repository.user_repository import UserRepository


class FriendshipService:
    """Friendship service for request handling, status updates, and relationship queries."""
    
    def __init__(self):
        self.friendship_repo = FriendshipRepository()
        self.user_repo = UserRepository()
        
    def request_friendship(
        self, requestor_id: int, requested_id: int, db: Session
    ) -> models.Friendship:
        """
        Send a friend request from current user to target user.
        """
        if requestor_id == requested_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot send a friend request to yourself"
            )
            
        # Verify requested user exists
        if not self.user_repo.read(db, requested_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found"
            )
            
        # Check if relation already exists in either direction
        existing = self.friendship_repo.find_friendship_bidirectional(db, requestor_id, requested_id)
        
        if existing:
            if existing.status == "accepted":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You are already friends with this user"
                )
            elif existing.status == "pending":
                if existing.requestor_id == requestor_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="You have already sent a pending request to this user"
                    )
                else:
                    # Target user sent a request to current user, so accept it!
                    existing.status = "accepted"
                    existing.updated_at = datetime.now(timezone.utc)
                    db.commit()
                    db.refresh(existing)
                    return existing
            elif existing.status == "blocked":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This friendship status is blocked"
                )
            elif existing.status == "rejected":
                # Resend the request
                existing.requestor_id = requestor_id
                existing.requested_id = requested_id
                existing.status = "pending"
                existing.created_at = datetime.now(timezone.utc)
                existing.updated_at = None
                db.commit()
                db.refresh(existing)
                return existing

        # Create new pending request
        friendship = self.friendship_repo.create(
            db,
            {
                "requestor_id": requestor_id,
                "requested_id": requested_id,
                "status": "pending"
            }
        )
        return friendship

    def get_friendship(self, friendship_id: UUID, db: Session) -> models.Friendship:
        """Fetch friendship by UUID."""
        friendship = self.friendship_repo.read(db, friendship_id)
        if not friendship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Friendship relationship not found"
            )
        return friendship

    def update_friendship_status(
        self, user_id: int, friendship_id: UUID, new_status: str, db: Session
    ) -> models.Friendship:
        """
        Accept, reject, or block a friendship request.
        """
        friendship = self.get_friendship(friendship_id, db)
        
        if new_status not in ["accepted", "rejected", "blocked"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status update"
            )

        if new_status in ["accepted", "rejected"]:
            # Only the recipient of the request can accept or reject it
            if friendship.requested_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to respond to this request"
                )
            if friendship.status != "pending":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot update status from {friendship.status} to {new_status}"
                )
        
        if new_status == "blocked":
            # Either user can block the other
            if friendship.requestor_id != user_id and friendship.requested_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this relationship"
                )
            # Ensure blocker is stored as requestor_id, and blocked as requested_id
            if friendship.requested_id == user_id:
                friendship.requested_id = friendship.requestor_id
                friendship.requestor_id = user_id

        friendship.status = new_status
        friendship.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(friendship)
        return friendship

    def block_user_explicit(
        self, user_id: int, target_user_id: int, db: Session
    ) -> models.Friendship:
        """
        Block a user directly. Creates relationship if none exists.
        """
        if user_id == target_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot block yourself"
            )
            
        # Verify target user exists
        if not self.user_repo.read(db, target_user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found"
            )

        existing = self.friendship_repo.find_friendship_bidirectional(db, user_id, target_user_id)
        if existing:
            # Change status to blocked, blocker becomes requestor_id
            existing.requestor_id = user_id
            existing.requested_id = target_user_id
            existing.status = "blocked"
            existing.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            return existing

        # Create new blocked relation
        friendship = self.friendship_repo.create(
            db,
            {
                "requestor_id": user_id,
                "requested_id": target_user_id,
                "status": "blocked"
            }
        )
        return friendship

    def cancel_friend_request(
        self, user_id: int, friendship_id: UUID, db: Session
    ) -> bool:
        """
        Cancel a pending friend request sent by current user.
        """
        friendship = self.get_friendship(friendship_id, db)
        
        if friendship.requestor_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to cancel this request"
            )
            
        if friendship.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel a non-pending request"
            )
            
        db.delete(friendship)
        db.commit()
        return True

    def remove_friendship(
        self, user_id: int, friendship_id: UUID, db: Session
    ) -> bool:
        """
        Remove an accepted friendship.
        """
        friendship = self.get_friendship(friendship_id, db)
        
        if friendship.requestor_id != user_id and friendship.requested_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to remove this relationship"
            )
            
        if friendship.status != "accepted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove a non-accepted friendship"
            )
            
        db.delete(friendship)
        db.commit()
        return True

    def get_friends_list(
        self, user_id: int, db: Session, skip: int = 0, limit: int = 100
    ) -> List[models.Friendship]:
        """Get list of active friends."""
        return self.friendship_repo.get_user_friends(db, user_id, skip, limit)

    def get_pending_sent(
        self, user_id: int, db: Session, skip: int = 0, limit: int = 100
    ) -> List[models.Friendship]:
        """Get pending sent requests."""
        return self.friendship_repo.get_pending_requests_sent(db, user_id, skip, limit)

    def get_pending_received(
        self, user_id: int, db: Session, skip: int = 0, limit: int = 100
    ) -> List[models.Friendship]:
        """Get pending received requests."""
        return self.friendship_repo.get_pending_requests_received(db, user_id, skip, limit)

    def get_friendship_status_bidirectional(
        self, user_a: int, user_b: int, db: Session
    ) -> Optional[models.Friendship]:
        """Get friendship relationship between two users if any exists."""
        return self.friendship_repo.find_friendship_bidirectional(db, user_a, user_b)

    def get_friends_profiles(
        self, user_id: int, db: Session, skip: int = 0, limit: int = 100
    ) -> List[models.User]:
        """Get user objects representing active friends of a user."""
        friendships = self.friendship_repo.get_user_friends(db, user_id, skip, limit)
        friend_ids = []
        for f in friendships:
            if f.requestor_id == user_id:
                friend_ids.append(f.requested_id)
            else:
                friend_ids.append(f.requestor_id)
        
        friends = []
        for fid in friend_ids:
            u = self.user_repo.read(db, fid)
            if u:
                friends.append(u)
        return friends
