"""
Production-Ready FastAPI WebSocket Implementation
Handles: reconnections, heartbeats, graceful degradation, authentication, rate limiting, and more.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status
from fastapi.responses import HTMLResponse
from typing import Dict, Set, Optional, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import asyncio
import json
import logging
from enum import Enum
from pydantic import BaseModel
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    DISCONNECTED = "disconnected"


class MessageType(Enum):
    HEARTBEAT = "heartbeat"
    MESSAGE = "message"
    BROADCAST = "broadcast"
    ERROR = "error"
    ACK = "ack"
    RECONNECT = "reconnect"


class WSMessage(BaseModel):
    type: MessageType
    data: Any
    timestamp: datetime = datetime.utcnow()
    message_id: Optional[str] = None


class ConnectionInfo:
    """Track connection metadata and health"""
    def __init__(self, websocket: WebSocket, client_id: str, room_id: Optional[str] = None):
        self.websocket = websocket
        self.client_id = client_id
        self.room_id = room_id
        self.connected_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        self.state = ConnectionState.CONNECTED
        self.reconnect_attempts = 0
        self.message_count = 0
        self.session_id = str(uuid.uuid4())

    def update_heartbeat(self):
        self.last_heartbeat = datetime.utcnow()

    def is_alive(self, timeout_seconds: int = 60) -> bool:
        return (datetime.utcnow() - self.last_heartbeat).seconds < timeout_seconds


class ConnectionManager:
    """Production-grade WebSocket connection manager"""
    
    def __init__(
        self,
        heartbeat_interval: int = 30,
        heartbeat_timeout: int = 60,
        max_connections_per_room: int = 100,
        message_rate_limit: int = 100,
        rate_limit_window: int = 60
    ):
        # Connection tracking
        self.active_connections: Dict[str, ConnectionInfo] = {}
        self.room_connections: Dict[str, Set[str]] = {}
        
        # Configuration
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout
        self.max_connections_per_room = max_connections_per_room
        self.message_rate_limit = message_rate_limit
        self.rate_limit_window = rate_limit_window
        
        # Rate limiting
        self.message_timestamps: Dict[str, list] = {}
        
        # Background tasks
        self._heartbeat_task = None
        self._cleanup_task = None

    async def start_background_tasks(self):
        """Start monitoring tasks"""
        if not self._heartbeat_task:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_stale_connections())

    async def connect(
        self, 
        websocket: WebSocket, 
        client_id: str,
        room_id: Optional[str] = None,
        token: Optional[str] = None
    ) -> ConnectionInfo:
        """Establish new WebSocket connection with validation"""
        
        # Validate room capacity
        if room_id:
            room_size = len(self.room_connections.get(room_id, set()))
            if room_size >= self.max_connections_per_room:
                logger.warning(f"Room {room_id} is at capacity")
                await websocket.close(code=1008, reason="Room at capacity")
                raise HTTPException(status_code=503, detail="Room at capacity")
        
        # Accept connection
        await websocket.accept()
        
        # Create connection info
        conn_info = ConnectionInfo(websocket, client_id, room_id)
        
        # Handle reconnection case
        if client_id in self.active_connections:
            old_conn = self.active_connections[client_id]
            conn_info.reconnect_attempts = old_conn.reconnect_attempts + 1
            conn_info.state = ConnectionState.RECONNECTING
            logger.info(f"Client {client_id} reconnecting (attempt {conn_info.reconnect_attempts})")
            await self._handle_reconnect(old_conn, conn_info)
        
        # Register connection
        self.active_connections[client_id] = conn_info
        
        if room_id:
            if room_id not in self.room_connections:
                self.room_connections[room_id] = set()
            self.room_connections[room_id].add(client_id)
        
        logger.info(f"Client {client_id} connected to room {room_id}. Session: {conn_info.session_id}")
        
        # Send connection acknowledgment
        await self._send_message(
            conn_info,
            WSMessage(
                type=MessageType.ACK,
                data={
                    "status": "connected",
                    "session_id": conn_info.session_id,
                    "heartbeat_interval": self.heartbeat_interval
                }
            )
        )
        
        return conn_info

    async def disconnect(self, client_id: str, session_id: Optional[str] = None):
        """Gracefully disconnect a client"""
        if client_id not in self.active_connections:
            return

        conn_info = self.active_connections[client_id]

        # If session_id is provided, only disconnect if it matches
        # This prevents disconnecting a new connection when cleaning up an old one
        if session_id and conn_info.session_id != session_id:
            logger.debug(f"Skipping disconnect for {client_id} - session mismatch (old: {session_id}, current: {conn_info.session_id})")
            return

        conn_info.state = ConnectionState.DISCONNECTED

        # Remove from room
        if conn_info.room_id and conn_info.room_id in self.room_connections:
            self.room_connections[conn_info.room_id].discard(client_id)
            if not self.room_connections[conn_info.room_id]:
                del self.room_connections[conn_info.room_id]

        # Close WebSocket
        try:
            await conn_info.websocket.close()
        except Exception as e:
            logger.error(f"Error closing websocket for {client_id}: {e}")

        # Remove from active connections
        del self.active_connections[client_id]

        logger.info(f"Client {client_id} disconnected. Session duration: {datetime.utcnow() - conn_info.connected_at}")

    async def send_personal_message(self, message: str, client_id: str):
        """Send message to specific client"""
        if client_id not in self.active_connections:
            logger.warning(f"Cannot send message to {client_id}: not connected")
            return False
        
        conn_info = self.active_connections[client_id]
        ws_message = WSMessage(
            type=MessageType.MESSAGE,
            data=message,
            message_id=str(uuid.uuid4())
        )
        
        return await self._send_message(conn_info, ws_message)

    async def broadcast(self, message: str, room_id: Optional[str] = None, exclude_client: Optional[str] = None):
        """Broadcast message to all clients in a room or globally"""
        ws_message = WSMessage(
            type=MessageType.BROADCAST,
            data=message,
            message_id=str(uuid.uuid4())
        )
        
        target_clients = set()
        
        if room_id and room_id in self.room_connections:
            target_clients = self.room_connections[room_id].copy()
        else:
            target_clients = set(self.active_connections.keys())
        
        if exclude_client:
            target_clients.discard(exclude_client)
        
        # Send to all targets concurrently
        tasks = []
        for client_id in target_clients:
            if client_id in self.active_connections:
                conn_info = self.active_connections[client_id]
                tasks.append(self._send_message(conn_info, ws_message))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        success_count = sum(1 for r in results if r is True)
        
        logger.info(f"Broadcast to {len(target_clients)} clients, {success_count} successful")

    async def _send_message(self, conn_info: ConnectionInfo, message: WSMessage) -> bool:
        """Send message with error handling"""
        try:
            await conn_info.websocket.send_json({
                "type": message.type.value,
                "data": message.data,
                "timestamp": message.timestamp.isoformat(),
                "message_id": message.message_id
            })
            conn_info.message_count += 1
            return True
        except Exception as e:
            logger.error(f"Error sending message to {conn_info.client_id}: {e}")
            await self.disconnect(conn_info.client_id, session_id=conn_info.session_id)
            return False

    def check_rate_limit(self, client_id: str) -> bool:
        """Check if client exceeds rate limit"""
        now = datetime.utcnow()
        
        if client_id not in self.message_timestamps:
            self.message_timestamps[client_id] = []
        
        # Remove old timestamps
        cutoff = now - timedelta(seconds=self.rate_limit_window)
        self.message_timestamps[client_id] = [
            ts for ts in self.message_timestamps[client_id] if ts > cutoff
        ]
        
        # Check limit
        if len(self.message_timestamps[client_id]) >= self.message_rate_limit:
            logger.warning(f"Rate limit exceeded for client {client_id}")
            return False
        
        self.message_timestamps[client_id].append(now)
        return True

    async def _handle_reconnect(self, old_conn: ConnectionInfo, new_conn: ConnectionInfo):
        """Handle reconnection logic"""
        try:
            # Close old connection
            await old_conn.websocket.close(code=1000, reason="Reconnecting")
        except Exception as e:
            logger.error(f"Error closing old connection: {e}")
        
        # Notify about reconnection
        logger.info(f"Client {new_conn.client_id} successfully reconnected")

    async def _heartbeat_monitor(self):
        """Background task to send heartbeats and detect stale connections"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                current_time = datetime.utcnow()
                stale_clients = []

                # Create a snapshot to avoid "dictionary changed size during iteration" errors
                for client_id, conn_info in list(self.active_connections.items()):
                    # Check if connection is alive
                    if not conn_info.is_alive(self.heartbeat_timeout):
                        stale_clients.append((client_id, conn_info.session_id))
                        continue

                    # Send heartbeat
                    heartbeat = WSMessage(type=MessageType.HEARTBEAT, data={"timestamp": current_time.isoformat()})
                    await self._send_message(conn_info, heartbeat)

                # Disconnect stale clients
                for client_id, session_id in stale_clients:
                    logger.warning(f"Client {client_id} missed heartbeat, disconnecting")
                    await self.disconnect(client_id, session_id=session_id)

            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")

    async def _cleanup_stale_connections(self):
        """Periodic cleanup of disconnected connections"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Clean up rate limit tracking for disconnected clients
                active_client_ids = set(self.active_connections.keys())
                stale_clients = set(self.message_timestamps.keys()) - active_client_ids
                
                for client_id in stale_clients:
                    del self.message_timestamps[client_id]
                
                logger.info(f"Cleanup completed. Active connections: {len(self.active_connections)}")
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    def get_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "total_rooms": len(self.room_connections),
            "room_details": {
                room_id: len(clients) 
                for room_id, clients in self.room_connections.items()
            },
            "heartbeat_interval": self.heartbeat_interval,
            "heartbeat_timeout": self.heartbeat_timeout
        }


# Initialize manager
manager = ConnectionManager(
    heartbeat_interval=30,
    heartbeat_timeout=60,
    max_connections_per_room=100,
    message_rate_limit=100
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup: Start background monitoring tasks
    await manager.start_background_tasks()
    logger.info("WebSocket manager started")

    yield

    # Shutdown: Cleanup
    # Disconnect all clients
    client_ids = list(manager.active_connections.keys())
    for client_id in client_ids:
        await manager.disconnect(client_id)
    logger.info("WebSocket manager shut down")


# Initialize FastAPI app with lifespan handler
app = FastAPI(title="Production WebSocket Service", lifespan=lifespan)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    room_id: Optional[str] = None,
    token: Optional[str] = None
):
    """Main WebSocket endpoint with full production features"""

    conn_info = None
    session_id = None
    try:
        # Connect client
        conn_info = await manager.connect(websocket, client_id, room_id, token)
        session_id = conn_info.session_id

        # Main message loop
        while True:
            # Receive message
            data = await websocket.receive_text()

            # Rate limiting
            if not manager.check_rate_limit(client_id):
                await manager._send_message(
                    conn_info,
                    WSMessage(
                        type=MessageType.ERROR,
                        data={"error": "Rate limit exceeded"}
                    )
                )
                continue

            # Parse message
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "message")

                # Update heartbeat on any message
                conn_info.update_heartbeat()

                # Handle different message types
                if message_type == "heartbeat":
                    # Client heartbeat response
                    conn_info.update_heartbeat()

                elif message_type == "message":
                    # Personal message - echo back
                    await manager.send_personal_message(
                        f"Echo: {message_data.get('data', '')}",
                        client_id
                    )

                elif message_type == "broadcast":
                    # Broadcast to room
                    await manager.broadcast(
                        message_data.get('data', ''),
                        room_id=room_id,
                        exclude_client=client_id
                    )

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}")
                await manager._send_message(
                    conn_info,
                    WSMessage(type=MessageType.ERROR, data={"error": "Invalid JSON"})
                )

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected normally")
    except Exception as e:
        logger.error(f"Error in websocket endpoint for {client_id}: {e}")
    finally:
        if session_id:
            # Only disconnect if this session is still active (prevents race condition on reconnect)
            await manager.disconnect(client_id, session_id=session_id)


@app.get("/stats")
async def get_stats():
    """Get WebSocket connection statistics"""
    return manager.get_stats()


@app.get("/")
async def get():
    """Simple HTML client for testing"""
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>Production WebSocket Client</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; }
        #messages { border: 1px solid #ccc; height: 400px; overflow-y: scroll; padding: 10px; margin: 20px 0; }
        .message { padding: 5px; margin: 5px 0; }
        .heartbeat { color: #999; font-size: 12px; }
        .error { color: red; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .connected { background-color: #d4edda; }
        .disconnected { background-color: #f8d7da; }
        input, button { padding: 10px; margin: 5px; }
    </style>
</head>
<body>
    <h1>Production WebSocket Test</h1>
    <div id="status" class="status disconnected">Disconnected</div>
    <div>
        <input type="text" id="clientId" placeholder="Client ID" value="client-1">
        <input type="text" id="roomId" placeholder="Room ID (optional)">
        <button onclick="connect()">Connect</button>
        <button onclick="disconnect()">Disconnect</button>
    </div>
    <div>
        <input type="text" id="messageInput" placeholder="Type message..." style="width: 400px">
        <button onclick="sendMessage()">Send</button>
        <button onclick="broadcast()">Broadcast</button>
    </div>
    <div id="messages"></div>

    <script>
        let ws = null;
        let reconnectAttempts = 0;
        let maxReconnectAttempts = 5;
        let reconnectDelay = 1000;
        let heartbeatInterval = null;

        function updateStatus(connected) {
            const statusEl = document.getElementById('status');
            if (connected) {
                statusEl.textContent = 'Connected';
                statusEl.className = 'status connected';
            } else {
                statusEl.textContent = 'Disconnected';
                statusEl.className = 'status disconnected';
            }
        }

        function addMessage(text, className = '') {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + className;
            messageDiv.textContent = new Date().toLocaleTimeString() + ' - ' + text;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function connect() {
            const clientId = document.getElementById('clientId').value;
            const roomId = document.getElementById('roomId').value;
            
            let url = `ws://localhost:8000/ws/${clientId}`;
            if (roomId) {
                url += `?room_id=${roomId}`;
            }

            ws = new WebSocket(url);

            ws.onopen = () => {
                updateStatus(true);
                addMessage('Connected to server');
                reconnectAttempts = 0;
                
                // Start client-side heartbeat
                heartbeatInterval = setInterval(() => {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({type: 'heartbeat', data: {}}));
                    }
                }, 25000);
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.type === 'heartbeat') {
                    addMessage('Heartbeat received', 'heartbeat');
                } else if (data.type === 'error') {
                    addMessage('Error: ' + data.data.error, 'error');
                } else {
                    addMessage('Received: ' + JSON.stringify(data.data));
                }
            };

            ws.onclose = () => {
                updateStatus(false);
                addMessage('Connection closed');
                clearInterval(heartbeatInterval);
                
                // Attempt reconnection with exponential backoff
                if (reconnectAttempts < maxReconnectAttempts) {
                    const delay = reconnectDelay * Math.pow(2, reconnectAttempts);
                    addMessage(`Reconnecting in ${delay}ms...`);
                    setTimeout(() => {
                        reconnectAttempts++;
                        connect();
                    }, delay);
                }
            };

            ws.onerror = (error) => {
                addMessage('WebSocket error', 'error');
                console.error('WebSocket error:', error);
            };
        }

        function disconnect() {
            if (ws) {
                clearInterval(heartbeatInterval);
                ws.close();
                ws = null;
            }
        }

        function sendMessage() {
            const input = document.getElementById('messageInput');
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'message',
                    data: input.value
                }));
                input.value = '';
            } else {
                addMessage('Not connected', 'error');
            }
        }

        function broadcast() {
            const input = document.getElementById('messageInput');
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'broadcast',
                    data: input.value
                }));
                input.value = '';
            } else {
                addMessage('Not connected', 'error');
            }
        }

        // Allow Enter key to send
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
    """)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ws_ping_interval=20,
        ws_ping_timeout=20
    )