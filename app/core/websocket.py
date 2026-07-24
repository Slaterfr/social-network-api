from fastapi import WebSocket
from typing import Dict, List
import uuid

class ConnectionManager:
    def __init__(self):
        # Maps community_id (uuid) to a list of active WebSockets
        self.active_connections: Dict[uuid.UUID, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, community_id: uuid.UUID):
        await websocket.accept()
        if community_id not in self.active_connections:
            self.active_connections[community_id] = []
        self.active_connections[community_id].append(websocket)

    def disconnect(self, websocket: WebSocket, community_id: uuid.UUID):
        if community_id in self.active_connections:
            if websocket in self.active_connections[community_id]:
                self.active_connections[community_id].remove(websocket)
            if not self.active_connections[community_id]:
                del self.active_connections[community_id]

    async def broadcast(self, community_id: uuid.UUID, message_data: dict):
        if community_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[community_id]:
                try:
                    await connection.send_json(message_data)
                except Exception:
                    dead_connections.append(connection)
            
            # Clean up any stale/broken connections discovered during broadcasting
            for dead in dead_connections:
                self.disconnect(dead, community_id)

manager = ConnectionManager()
