from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from fastapi import HTTPException, status
import uuid
from datetime import datetime, timezone, timedelta

from app import models, schemas
from app.repository.community_repository import CommunityRepository
from app.services.file_management import FileManagementService

class CommunityService:
    def __init__(self):
        self.community_repo = CommunityRepository()
        self.file_management = FileManagementService()

    def _attach_avatar_url(self, community: models.Community) -> models.Community:
        if community.avatar_key:
            try:
                community.avatar_url = self.file_management.generate_url(community.avatar_key)
            except Exception:
                community.avatar_url = None
        else:
            community.avatar_url = None
        return community

    def create_community(self, community_data: schemas.CommunityCreate, owner_id: int, db: Session) -> models.Community:
        # Check unique name
        existing = db.query(models.Community).filter(
            models.Community.name == community_data.name,
            models.Community.deleted_at.is_(None)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A community with this name already exists"
            )

        # Create community
        community = self.community_repo.create(
            db,
            {
                "name": community_data.name,
                "slogan": community_data.slogan,
                "privacy": community_data.privacy,
                "owner_id": owner_id
            }
        )

        # Automatically add owner as CommunityMember
        db.add(models.CommunityMember(
            user_id=owner_id,
            community_id=community.id,
            community_role="owner",
            status="active"
        ))
        db.commit()

        return self._attach_avatar_url(community)

    def get_public_communities(self, db: Session, skip: int = 0, limit: int = 100, current_user_id: Optional[int] = None) -> List[models.Community]:
        communities = self.community_repo.find_all_public(db, skip, limit)
        for c in communities:
            self._attach_avatar_url(c)
            c.member_count = self.community_repo.get_member_count(db, c.id)
            if current_user_id:
                c.role_in_community = self.community_repo.get_member_role(db, c.id, current_user_id)
                c.join_request_status = self.community_repo.get_join_request_status(db, c.id, current_user_id)
        return communities

    def get_user_communities(self, db: Session, user_id: int) -> List[models.Community]:
        communities = self.community_repo.find_user_communities(db, user_id)
        for c in communities:
            self._attach_avatar_url(c)
            c.member_count = self.community_repo.get_member_count(db, c.id)
            c.role_in_community = self.community_repo.get_member_role(db, c.id, user_id)
        return communities

    def get_community(self, community_id: uuid.UUID, db: Session, current_user_id: Optional[int] = None) -> models.Community:
        community = self.community_repo.read(db, community_id)
        if not community or community.deleted_at:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Community not found"
            )

        self._attach_avatar_url(community)
        community.member_count = self.community_repo.get_member_count(db, community.id)
        if current_user_id:
            community.role_in_community = self.community_repo.get_member_role(db, community.id, current_user_id)
            community.join_request_status = self.community_repo.get_join_request_status(db, community.id, current_user_id)

        # Privacy gate checks
        if community.privacy == "private" and not community.role_in_community:
            # Check if user has a pending invitation
            invited = db.query(models.CommunityJoinRequest).filter(
                models.CommunityJoinRequest.community_id == community.id,
                models.CommunityJoinRequest.user_id == current_user_id,
                models.CommunityJoinRequest.status == "invited"
            ).first()
            if not invited:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This community is private and invite-only"
                )
            else:
                community.join_request_status = "invited"
                community.join_request_id = invited.id

        return community

    def update_community_avatar(self, community_id: uuid.UUID, avatar_key: str, current_user: models.User, db: Session) -> models.Community:
        community = self.get_community(community_id, db, current_user.id)
        if community.owner_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the community owner or an admin can update the avatar"
            )

        updated = self.community_repo.update(
            db, community_id, {"avatar_key": avatar_key, "modified_at": datetime.now(timezone.utc)}
        )
        return self._attach_avatar_url(updated)

    def delete_community(self, community_id: uuid.UUID, current_user: models.User, db: Session):
        community = self.get_community(community_id, db, current_user.id)
        if community.owner_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the community owner or an admin can delete it"
            )

        self.community_repo.update(
            db, community_id, {"deleted_at": datetime.now(timezone.utc)}
        )

    # Membership & Join Requests
    def join_community(self, community_id: uuid.UUID, user_id: int, db: Session):
        community = db.query(models.Community).filter(
            models.Community.id == community_id,
            models.Community.deleted_at.is_(None)
        ).first()

        if not community:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Community not found"
            )

        # Check if user has an invitation
        invited = db.query(models.CommunityJoinRequest).filter(
            models.CommunityJoinRequest.community_id == community_id,
            models.CommunityJoinRequest.user_id == user_id,
            models.CommunityJoinRequest.status == "invited"
        ).first()

        if community.privacy == "public" or invited:
            # Direct join
            member = db.query(models.CommunityMember).filter(
                models.CommunityMember.community_id == community_id,
                models.CommunityMember.user_id == user_id
            ).first()
            if member:
                member.status = "active"
                member.community_role = "member"
                member.joined_date = datetime.now(timezone.utc)
                member.date_left = None
            else:
                db.add(models.CommunityMember(
                    user_id=user_id,
                    community_id=community_id,
                    community_role="member",
                    status="active"
                ))
            if invited:
                db.delete(invited)
            db.commit()
            return {"status": "approved", "detail": "Joined successfully"}

        elif community.privacy == "listed":
            # Create Join Request
            existing_req = db.query(models.CommunityJoinRequest).filter(
                models.CommunityJoinRequest.community_id == community_id,
                models.CommunityJoinRequest.user_id == user_id
            ).first()
            if existing_req:
                if existing_req.status == "pending":
                    return {"status": "pending", "detail": "Join request already pending"}
                existing_req.status = "pending"
                existing_req.updated_at = datetime.now(timezone.utc)
            else:
                db.add(models.CommunityJoinRequest(
                    user_id=user_id,
                    community_id=community_id,
                    status="pending"
                ))
            db.commit()
            return {"status": "pending", "detail": "Request submitted"}

        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Private communities are invite-only"
            )

    def leave_community(self, community_id: uuid.UUID, user_id: int, db: Session):
        member = db.query(models.CommunityMember).filter(
            models.CommunityMember.community_id == community_id,
            models.CommunityMember.user_id == user_id,
            models.CommunityMember.status == "active"
        ).first()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are not a member of this community"
            )

        if member.community_role == "owner":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The owner cannot leave the community. Demote or transfer ownership first."
            )

        member.status = "inactive"
        member.date_left = datetime.now(timezone.utc)
        db.commit()

    def get_join_requests(self, community_id: uuid.UUID, current_user_id: int, db: Session) -> List[models.CommunityJoinRequest]:
        role = self.community_repo.get_member_role(db, community_id, current_user_id)
        if role not in ["owner", "moderator"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only community moderators or owners can view join requests"
            )
        return self.community_repo.find_join_requests(db, community_id)

    def handle_join_request(self, request_id: uuid.UUID, action: str, current_user_id: int, db: Session):
        req = db.query(models.CommunityJoinRequest).filter(
            models.CommunityJoinRequest.id == request_id
        ).first()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Join request not found"
            )

        # Allow target invited user to decline/reject their invitation
        is_invited_user = req.user_id == current_user_id and req.status == "invited"

        if not is_invited_user:
            role = self.community_repo.get_member_role(db, req.community_id, current_user_id)
            if role not in ["owner", "moderator"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only community moderators or owners can manage join requests"
                )

        if action == "approved":
            req.status = "approved"
            # Add member
            member = db.query(models.CommunityMember).filter(
                models.CommunityMember.community_id == req.community_id,
                models.CommunityMember.user_id == req.user_id
            ).first()
            if member:
                member.status = "active"
                member.community_role = "member"
                member.joined_date = datetime.now(timezone.utc)
                member.date_left = None
            else:
                db.add(models.CommunityMember(
                    user_id=req.user_id,
                    community_id=req.community_id,
                    community_role="member",
                    status="active"
                ))
        else:
            req.status = "rejected"

        req.updated_at = datetime.now(timezone.utc)
        db.commit()

    def get_community_members(self, community_id: uuid.UUID, current_user_id: int, db: Session) -> List[models.CommunityMember]:
        # Validate membership privacy gate
        self.get_community(community_id, db, current_user_id)
        return self.community_repo.find_members(db, community_id)

    def update_member_role(self, community_id: uuid.UUID, target_user_id: int, new_role: str, current_user_id: int, db: Session):
        # Only owner can update roles
        role = self.community_repo.get_member_role(db, community_id, current_user_id)
        if role != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the community owner can update member roles"
            )

        if target_user_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot change your own role. Demote or transfer ownership first."
            )

        member = db.query(models.CommunityMember).filter(
            models.CommunityMember.community_id == community_id,
            models.CommunityMember.user_id == target_user_id,
            models.CommunityMember.status == "active"
        ).first()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )

        if new_role not in ["member", "moderator", "owner"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid community role"
            )

        if new_role == "owner":
            # Transfer ownership
            # Demote current owner to moderator
            owner_member = db.query(models.CommunityMember).filter(
                models.CommunityMember.community_id == community_id,
                models.CommunityMember.user_id == current_user_id
            ).first()
            owner_member.community_role = "moderator"
            # Update community owner_id in parent table
            community = self.community_repo.read(db, community_id)
            community.owner_id = target_user_id

        member.community_role = new_role
        db.commit()

    def kick_member(self, community_id: uuid.UUID, target_user_id: int, current_user_id: int, db: Session):
        role = self.community_repo.get_member_role(db, community_id, current_user_id)
        if role not in ["owner", "moderator"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only moderators or owners can kick members"
            )

        target_member = db.query(models.CommunityMember).filter(
            models.CommunityMember.community_id == community_id,
            models.CommunityMember.user_id == target_user_id,
            models.CommunityMember.status == "active"
        ).first()

        if not target_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )

        # Moderator safety check: mods cannot kick owners or other mods
        if role == "moderator" and target_member.community_role in ["owner", "moderator"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Moderators cannot kick other moderators or owners"
            )

        if target_user_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot kick yourself"
            )

        target_member.status = "inactive"
        target_member.date_left = datetime.now(timezone.utc)
        db.commit()

    # WebSockets Messaging & Tickets
    def create_ws_ticket(self, user_id: int, db: Session) -> uuid.UUID:
        ticket = models.WebSocketTicket(user_id=user_id)
        db.add(ticket)
        db.commit()
        return ticket.ticket

    def validate_and_burn_ticket(self, ticket_uuid: uuid.UUID, db: Session) -> int:
        ticket = db.query(models.WebSocketTicket).filter(
            models.WebSocketTicket.ticket == ticket_uuid
        ).first()
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid connection ticket"
            )

        # Check age (< 30 seconds)
        now = datetime.now(timezone.utc)
        created_at_utc = ticket.created_at.replace(tzinfo=timezone.utc)
        if now - created_at_utc > timedelta(seconds=30):
            # Burn anyway to prevent reuse
            db.delete(ticket)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Connection ticket has expired"
            )

        user_id = ticket.user_id
        # Burn ticket
        db.delete(ticket)
        db.commit()
        return user_id

    def get_messages(self, community_id: uuid.UUID, current_user_id: int, db: Session, limit: int = 50) -> List[models.CommunityMessage]:
        # Validate privacy gate
        self.get_community(community_id, db, current_user_id)
        
        messages = self.community_repo.find_messages(db, community_id, limit)
        for msg in messages:
            if msg.reply_to_message_id:
                parent = db.query(models.CommunityMessage).filter(models.CommunityMessage.id == msg.reply_to_message_id).first()
                if parent:
                    msg.replied_to_message_content = parent.content
                    parent_user = db.query(models.User).filter(models.User.id == parent.issuer_id).first()
                    msg.replied_to_message_username = parent_user.username if parent_user else "Unknown"
        return messages

    def save_message(self, community_id: uuid.UUID, issuer_id: int, message_data: schemas.CommunityMessageCreate, db: Session) -> models.CommunityMessage:
        # Validate member status
        role = self.community_repo.get_member_role(db, community_id, issuer_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a member of this community to send messages"
            )

        msg = models.CommunityMessage(
            community_id=community_id,
            issuer_id=issuer_id,
            content=message_data.content,
            reply_to_message_id=message_data.reply_to_message_id,
            message_type=message_data.message_type
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        
        # Populate username and replies context for broadcasting
        msg.user = db.query(models.User).filter(models.User.id == issuer_id).first()
        if msg.reply_to_message_id:
            parent = db.query(models.CommunityMessage).filter(models.CommunityMessage.id == msg.reply_to_message_id).first()
            if parent:
                msg.replied_to_message_content = parent.content
                parent_user = db.query(models.User).filter(models.User.id == parent.issuer_id).first()
                msg.replied_to_message_username = parent_user.username if parent_user else "Unknown"

        return msg

    def delete_message(self, message_id: uuid.UUID, current_user_id: int, db: Session) -> models.CommunityMessage:
        msg = db.query(models.CommunityMessage).filter(
            models.CommunityMessage.id == message_id,
            models.CommunityMessage.deleted_at.is_(None)
        ).first()

        if not msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

        # Check authorization: author, mod, or owner
        role = self.community_repo.get_member_role(db, msg.community_id, current_user_id)
        is_author = msg.issuer_id == current_user_id
        
        if not is_author and role not in ["owner", "moderator"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this message"
            )

        # Moderator safety check: mods cannot delete owner messages unless they sent them
        if role == "moderator" and not is_author:
            # Check target author's role
            target_role = self.community_repo.get_member_role(db, msg.community_id, msg.issuer_id)
            if target_role == "owner":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Moderators cannot delete the owner's messages"
                )

        msg.deleted_at = datetime.now(timezone.utc)
        db.commit()
        return msg

    def invite_user_to_community(self, community_id: uuid.UUID, username: str, current_user_id: int, db: Session):
        # 1. Fetch community & verify current user role is owner or moderator
        community = self.get_community(community_id, db, current_user_id)
        role = community.role_in_community
        if role not in ["owner", "moderator"] and community.owner_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only community owners and moderators can invite members"
            )

        # 2. Get target user by username
        target_user = db.query(models.User).filter(
            models.User.username.ilike(username)
        ).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # 3. Check if target user is already a member
        member = db.query(models.CommunityMember).filter(
            models.CommunityMember.community_id == community_id,
            models.CommunityMember.user_id == target_user.id,
            models.CommunityMember.status == "active"
        ).first()
        if member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this community"
            )

        # 4. Check if request/invite already exists
        existing_invite = db.query(models.CommunityJoinRequest).filter(
            models.CommunityJoinRequest.community_id == community_id,
            models.CommunityJoinRequest.user_id == target_user.id
        ).first()
        if existing_invite:
            if existing_invite.status == "invited":
                return {"status": "invited", "detail": "User is already invited"}
            elif existing_invite.status == "pending":
                # Convert pending request to approved membership instantly!
                db.delete(existing_invite)
                db.add(models.CommunityMember(
                    user_id=target_user.id,
                    community_id=community_id,
                    community_role="member",
                    status="active"
                ))
                db.commit()
                return {"status": "approved", "detail": "Approved pending join request"}

        # 5. Create invitation
        db.add(models.CommunityJoinRequest(
            user_id=target_user.id,
            community_id=community_id,
            status="invited"
        ))
        db.commit()
        return {"status": "invited", "detail": "Invitation sent successfully"}

    def get_user_invitations(self, db: Session, user_id: int) -> List[models.Community]:
        # Find all join requests with status "invited" for this user
        requests = db.query(models.CommunityJoinRequest).filter(
            models.CommunityJoinRequest.user_id == user_id,
            models.CommunityJoinRequest.status == "invited"
        ).all()
        
        communities = []
        for req in requests:
            community = db.query(models.Community).filter(
                models.Community.id == req.community_id,
                models.Community.deleted_at.is_(None)
            ).first()
            if community:
                self._attach_avatar_url(community)
                community.member_count = self.community_repo.get_member_count(db, community.id)
                community.role_in_community = None
                community.join_request_status = "invited"
                community.join_request_id = req.id
                communities.append(community)
        return communities
