"""
Step 4: Message Structure & Types
Learn JSON messages, Pydantic validation, and message types
"""

from enum import Enum
from typing import Any, Optional
from datetime import datetime
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

app = FastAPI()


# TODO: Define MessageType enum with: MESSAGE, BROADCAST, ERROR, SYSTEM
class MessageType(str, Enum):
    MESSAGE = "message"
    BROADCAST = "broadcast"
    ERROR = "error"
    SYSTEM = "system"


# TODO: Create WSMessage Pydantic model
class WSMessage(BaseModel):
    type: MessageType
    data: str
    timestamp: datetime = datetime.now()
    message_id: Optional[str] = str(uuid4())
    sender: Optional[str] = None

    """
    Structured message format with validation

    Fields to include:
    - type: MessageType
    - data: Any (the actual message content)
    - timestamp: datetime (auto-generated)
    - message_id: Optional[str] (unique ID)
    - sender: Optional[str] (client_id of sender)
    """
    pass  # Fill in the model fields


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.room_connections: dict[str, set[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str, room_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        if room_id not in self.room_connections:
            self.room_connections[room_id] = set()
        self.room_connections[room_id].add(client_id)

    async def send_message(self, client_id: str, message: WSMessage):
        """
        TODO: Send a structured message to a specific client

        Hints:
        - Use websocket.send_json() instead of send_text()
        - Convert the Pydantic model to dict with message.model_dump()
        - Handle exceptions if client disconnected
        """
        
        
        
        pass  # Implement this

    async def broadcast_to_room(self, room_id: str, message: WSMessage):
        """
        TODO: Broadcast a structured message to all clients in a room

        Hints:
        - Iterate through clients in room_connections[room_id]
        - Use self.send_message() for each client
        - Handle exceptions gracefully
        """
        pass  # Implement this

    def disconnect(self, client_id: str, room_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if room_id in self.room_connections:
            self.room_connections[room_id].discard(client_id)
            if len(self.room_connections[room_id]) == 0:
                del self.room_connections[room_id]


manager = ConnectionManager()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    room_id: str = "lobby",
):
    await manager.connect(websocket, client_id, room_id)

    # TODO: Send welcome message using WSMessage
    # Type: SYSTEM, Data: "Welcome {client_id}!"
    # Hint: Create a WSMessage object and use manager.send_message()

    # TODO: Broadcast join notification to room
    # Type: SYSTEM, Data: "{client_id} joined the room"
    # Hint: Use manager.broadcast_to_room()

    try:
        while True:
            # TODO: Receive JSON message instead of text
            # Hint: Use websocket.receive_json()
            data = None  # Replace with actual receive

            # TODO: Parse the received data into WSMessage
            # Hint: Use WSMessage(**data) or WSMessage.model_validate(data)
            # Add error handling for invalid JSON/validation errors

            # TODO: Handle different message types
            # If type is MESSAGE: broadcast to room with sender info
            # If type is ERROR: handle error
            # Add message_id using str(uuid4())

            pass  # Implement message handling logic

    except WebSocketDisconnect:
        manager.disconnect(client_id, room_id)
        # TODO: Send leave notification to room
        # Type: SYSTEM, Data: "{client_id} left the room"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
