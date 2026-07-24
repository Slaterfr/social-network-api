from fastapi import APIRouter, Depends, status, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import json

from app import schemas, models
from app.repository.database import get_db
from app.dependencies.auth import get_current_user
from app.services.community_service import CommunityService
from app.services.file_management import FileManagementService
from app.core.websocket import manager

router = APIRouter(
    prefix="/communities",
    tags=["Communities"]
)

community_service = CommunityService()
file_management_service = FileManagementService()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.CommunityResponse)
def create_community(
    community_data: schemas.CommunityCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return community_service.create_community(community_data, current_user.id, db)


@router.get("/", response_model=List[schemas.CommunityResponse])
def get_communities(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user)
):
    return community_service.get_public_communities(db, skip, limit, current_user.id)


@router.get("/my", response_model=List[schemas.CommunityResponse])
def get_my_communities(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return community_service.get_user_communities(db, current_user.id)


@router.post("/ws-ticket", status_code=status.HTTP_201_CREATED)
def get_ws_ticket(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    ticket = community_service.create_ws_ticket(current_user.id, db)
    return {"ticket": str(ticket)}


@router.get("/{id}", response_model=schemas.CommunityResponse)
def get_community_details(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return community_service.get_community(id, db, current_user.id)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_community(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    community_service.delete_community(id, current_user, db)
    return None


@router.post("/{id}/avatar", response_model=schemas.CommunityResponse)
async def upload_community_avatar(
    id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Validate community ownership first
    community_service.get_community(id, db, current_user.id)
    
    # Save file
    uploaded_file = await file_management_service.save_file(file, current_user.id, db)
    return community_service.update_community_avatar(id, uploaded_file.storage_key, current_user, db)


# Membership operations
@router.post("/{id}/join", status_code=status.HTTP_200_OK)
def join_community(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return community_service.join_community(id, current_user.id, db)


@router.post("/{id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_community(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    community_service.leave_community(id, current_user.id, db)
    return None


@router.get("/{id}/members", response_model=List[schemas.CommunityMemberResponse])
def get_members(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return community_service.get_community_members(id, current_user.id, db)


@router.put("/{id}/members/{user_id}/role", response_model=schemas.CommunityMemberResponse)
def update_member_role(
    id: uuid.UUID,
    user_id: int,
    role_data: schemas.MemberRoleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    community_service.update_member_role(id, user_id, role_data.community_role, current_user.id, db)
    # Return updated member profile
    member = db.query(models.CommunityMember).filter(
        models.CommunityMember.community_id == id,
        models.CommunityMember.user_id == user_id
    ).first()
    return member


@router.delete("/{id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def kick_member(
    id: uuid.UUID,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    community_service.kick_member(id, user_id, current_user.id, db)
    return None


# Join Requests management
@router.get("/{id}/join-requests", response_model=List[schemas.CommunityJoinRequestResponse])
def get_pending_join_requests(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return community_service.get_join_requests(id, current_user.id, db)


@router.put("/{id}/join-requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def resolve_join_request(
    id: uuid.UUID,
    request_id: uuid.UUID,
    action_data: schemas.JoinRequestAction,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    community_service.handle_join_request(request_id, action_data.status, current_user.id, db)
    return None


# Chat Messages
@router.get("/{id}/messages", response_model=List[schemas.CommunityMessageResponse])
def get_messages(
    id: uuid.UUID,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return community_service.get_messages(id, current_user.id, db, limit)


@router.delete("/{id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    id: uuid.UUID,
    message_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    community_service.delete_message(message_id, current_user.id, db)
    # Broadcast deletion to all connected websockets
    await manager.broadcast(id, {
        "event": "delete_message",
        "data": {
            "message_id": str(message_id)
        }
    })
    return None


# WebSocket real-time chat room connection
@router.websocket("/{id}/ws")
async def community_ws_endpoint(
    websocket: WebSocket,
    id: uuid.UUID,
    ticket: str,
    db: Session = Depends(get_db)
):
    # Parse ticket UUID
    try:
        ticket_uuid = uuid.UUID(ticket)
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Validate and burn ticket
    try:
        user_id = community_service.validate_and_burn_ticket(ticket_uuid, db)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Connect to room manager
    await manager.connect(websocket, id)
    try:
        while True:
            # Listen for client text messages
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                content = payload.get("content", "").strip()
                reply_to_message_id_str = payload.get("reply_to_message_id")
                
                reply_to_message_id = None
                if reply_to_message_id_str:
                    try:
                        reply_to_message_id = uuid.UUID(reply_to_message_id_str)
                    except ValueError:
                        pass
                
                if not content:
                    continue

                msg_create = schemas.CommunityMessageCreate(
                    content=content,
                    reply_to_message_id=reply_to_message_id
                )
                
                # Save message
                saved_msg = community_service.save_message(id, user_id, msg_create, db)
                
                # Serialize response using schemas
                msg_response = schemas.CommunityMessageResponse.model_validate(saved_msg)
                
                # Broadcast message to room
                await manager.broadcast(id, {
                    "event": "new_message",
                    "data": json.loads(msg_response.model_dump_json())
                })
            except Exception as e:
                print("WS payload processing error:", e)
                continue
    except WebSocketDisconnect:
        manager.disconnect(websocket, id)
