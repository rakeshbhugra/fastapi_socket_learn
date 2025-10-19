# FastAPI WebSocket Learning Plan
## Learn Production WebSocket Development Step-by-Step

This learning plan breaks down the production WebSocket implementation into progressive steps, from basic to advanced. Each step builds on the previous one.

---

## 📚 Prerequisites
- Basic Python knowledge
- Understanding of async/await
- Basic HTTP/REST API concepts
- FastAPI basics (routes, dependencies)

---

## Step 1: Hello WebSocket (30 mins)
**Concepts:** Basic WebSocket connection, send/receive

### What You'll Build:
- Simple WebSocket endpoint
- Echo server (receives message, sends it back)
- Basic HTML client

### Key Learning:
- `@app.websocket()` decorator
- `websocket.accept()`, `websocket.send_text()`, `websocket.receive_text()`
- WebSocketDisconnect exception
- Basic client-side WebSocket API

### Exercise:
```python
# Create simple_echo.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")
```

### Tasks:
- [ ] Create the echo server
- [ ] Test with simple HTML client
- [ ] Add print statements to understand connection lifecycle
- [ ] Try disconnecting and see what happens

---

## Step 2: Multiple Clients & Broadcasting (1 hour)
**Concepts:** Connection management, broadcasting to multiple clients

### What You'll Build:
- Connection manager to track multiple clients
- Broadcast messages to all connected clients
- Personal messages to specific clients

### Key Learning:
- Managing connections in a dictionary/set
- Broadcasting patterns
- Client identification
- Concurrent message sending with `asyncio.gather()`

### Exercise:
```python
# Create broadcast_chat.py
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
```

### Tasks:
- [ ] Implement the ConnectionManager
- [ ] Create a chat endpoint that broadcasts messages
- [ ] Test with multiple browser tabs
- [ ] Add "User joined" and "User left" notifications
- [ ] Implement personal messages (direct messages)

---

## Step 3: Client Identity & Rooms (1.5 hours)
**Concepts:** Client IDs, room-based connections, targeted broadcasting

### What You'll Build:
- Unique client IDs
- Room/channel system
- Broadcast only to specific rooms
- Track client metadata

### Key Learning:
- Path parameters in WebSocket routes
- Query parameters for additional data
- Dictionary of sets for room management
- Filtering broadcast targets

### Exercise:
```python
# Add to ConnectionManager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.room_connections: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str, room_id: str):
        # Store by client_id, track rooms
        pass

    async def broadcast_to_room(self, message: str, room_id: str):
        # Send only to clients in specific room
        pass
```

### Tasks:
- [ ] Implement client_id in URL path: `/ws/{client_id}`
- [ ] Add room_id as query parameter: `?room_id=lobby`
- [ ] Track which clients are in which rooms
- [ ] Implement room-based broadcasting
- [ ] Test multiple clients in different rooms
- [ ] Add room capacity limits

---

## Step 4: Message Structure & Types (1 hour)
**Concepts:** JSON messages, message types, Pydantic models

### What You'll Build:
- Structured message format
- Different message types (chat, system, error)
- Message validation with Pydantic
- Message metadata (timestamp, ID)

### Key Learning:
- `websocket.send_json()` and `websocket.receive_json()`
- Pydantic BaseModel for validation
- Enum for message types
- Message IDs for tracking

### Exercise:
```python
from enum import Enum
from pydantic import BaseModel
from datetime import datetime

class MessageType(Enum):
    MESSAGE = "message"
    BROADCAST = "broadcast"
    ERROR = "error"
    SYSTEM = "system"

class WSMessage(BaseModel):
    type: MessageType
    data: Any
    timestamp: datetime = datetime.utcnow()
    message_id: Optional[str] = None
```

### Tasks:
- [ ] Create message models
- [ ] Update endpoints to use JSON messages
- [ ] Handle different message types
- [ ] Add error messages for invalid JSON
- [ ] Generate unique message IDs (uuid)
- [ ] Update client to send/receive JSON

---

## Step 5: Heartbeat & Connection Health (2 hours)
**Concepts:** Keep-alive, stale connection detection, background tasks

### What You'll Build:
- Server-side heartbeat sender
- Client response to heartbeats
- Detect and close stale connections
- Background monitoring task

### Key Learning:
- `asyncio.create_task()` for background tasks
- Time-based health checks
- Graceful connection cleanup
- Server-initiated messages

### Exercise:
```python
class ConnectionInfo:
    def __init__(self, websocket: WebSocket, client_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.last_heartbeat = datetime.utcnow()

    def update_heartbeat(self):
        self.last_heartbeat = datetime.utcnow()

    def is_alive(self, timeout_seconds: int = 60) -> bool:
        return (datetime.utcnow() - self.last_heartbeat).seconds < timeout_seconds

async def heartbeat_monitor():
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds
        # Send heartbeats, check for stale connections
```

### Tasks:
- [ ] Create ConnectionInfo class with metadata
- [ ] Implement heartbeat background task
- [ ] Send periodic heartbeat messages
- [ ] Update last_heartbeat on client messages
- [ ] Detect and disconnect stale connections
- [ ] Update client to respond to heartbeats

---

## Step 6: Rate Limiting (1.5 hours)
**Concepts:** Preventing abuse, sliding window rate limiting

### What You'll Build:
- Per-client message rate limiting
- Sliding time window
- Error responses for rate limit violations
- Cleanup of old timestamps

### Key Learning:
- Timestamp tracking
- Sliding window algorithm
- Timedelta calculations
- Graceful degradation

### Exercise:
```python
class ConnectionManager:
    def __init__(self, message_rate_limit: int = 100, rate_limit_window: int = 60):
        self.message_rate_limit = message_rate_limit
        self.rate_limit_window = rate_limit_window
        self.message_timestamps: Dict[str, list] = {}

    def check_rate_limit(self, client_id: str) -> bool:
        # Implement sliding window rate limiting
        pass
```

### Tasks:
- [ ] Implement timestamp tracking per client
- [ ] Create sliding window rate checker
- [ ] Return error message on rate limit
- [ ] Clean up old timestamps
- [ ] Test by spamming messages
- [ ] Make limits configurable

---

## Step 7: Reconnection Handling (2 hours)
**Concepts:** Session persistence, reconnection logic, race conditions

### What You'll Build:
- Detect client reconnections
- Session ID tracking
- Prevent race conditions on reconnect
- Graceful old connection cleanup
- Exponential backoff with jitter

### Key Learning:
- Session vs connection identity
- Race condition prevention
- State transfer on reconnect
- Idempotent operations
- Exponential backoff algorithm

### Exercise:
```python
class ConnectionInfo:
    def __init__(self, websocket: WebSocket, client_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.session_id = str(uuid.uuid4())
        self.reconnect_attempts = 0
        self.connected_at = datetime.utcnow()

async def disconnect(self, client_id: str, session_id: Optional[str] = None):
    # Only disconnect if session matches
    if session_id and conn_info.session_id != session_id:
        return  # Different session, skip

    # Proper close with code
    await websocket.close(code=1000, reason="Normal closure")

# Client-side exponential backoff with jitter
def get_reconnect_delay(attempt: int, base_delay: int = 1000) -> int:
    max_delay = 30000  # 30 seconds max
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = random.uniform(0, delay * 0.3)  # 30% jitter
    return delay + jitter
```

### Tasks:
- [ ] Add session_id to ConnectionInfo
- [ ] Detect when same client_id reconnects
- [ ] Increment reconnect counter
- [ ] Close old connection gracefully with proper close code
- [ ] Prevent race condition in cleanup
- [ ] Implement exponential backoff with jitter on client
- [ ] Add max reconnect attempts limit
- [ ] Test rapid reconnections
- [ ] Store session state for recovery

---

## Step 8: WebSocket Close Codes & Proper Shutdown (1 hour)
**Concepts:** WebSocket close protocol, status codes, clean shutdown

### What You'll Build:
- Proper close handshake
- WebSocket close codes (1000-1015)
- Graceful shutdown sequences
- Client notification on disconnect

### Key Learning:
- WebSocket close codes standard
- Two-way close handshake
- Reason strings
- Client-initiated vs server-initiated close

### Exercise:
```python
from enum import Enum

class CloseCode(Enum):
    NORMAL = 1000          # Normal closure
    GOING_AWAY = 1001      # Server shutting down
    PROTOCOL_ERROR = 1002  # Protocol error
    UNSUPPORTED = 1003     # Unsupported data
    INVALID_DATA = 1007    # Invalid frame payload
    POLICY_VIOLATION = 1008 # Policy violation
    MESSAGE_TOO_BIG = 1009 # Message too big
    INTERNAL_ERROR = 1011  # Server error

async def disconnect(self, client_id: str, code: int = 1000, reason: str = ""):
    if client_id in self.active_connections:
        conn = self.active_connections[client_id]
        try:
            await conn.websocket.close(code=code, reason=reason)
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
```

### Tasks:
- [ ] Create CloseCode enum with standard codes
- [ ] Update disconnect to accept code and reason
- [ ] Send proper close frames
- [ ] Handle different close scenarios (normal, error, timeout)
- [ ] Log close codes and reasons
- [ ] Test client receives close notification
- [ ] Implement close handshake (both sides)

---

## Step 9: Error Handling & Recovery (1.5 hours)
**Concepts:** Graceful failures, error types, recovery strategies

### What You'll Build:
- Try/catch around all operations
- Specific error types
- Error logging with context
- Automatic recovery
- User feedback on errors

### Key Learning:
- Exception hierarchies
- Logging best practices
- Partial failure handling
- Circuit breaker patterns
- User notification strategies

### Exercise:
```python
import logging

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def send_message(self, conn_info: ConnectionInfo, message: WSMessage) -> bool:
    try:
        await conn_info.websocket.send_json(...)
        conn_info.message_count += 1
        return True
    except ConnectionClosed as e:
        logger.warning(f"Connection closed for {conn_info.client_id}: {e}")
        await self.disconnect(conn_info.client_id, conn_info.session_id)
        return False
    except Exception as e:
        logger.error(f"Error sending message to {conn_info.client_id}: {e}", exc_info=True)
        await self.disconnect(conn_info.client_id, conn_info.session_id)
        return False

# Client-side error notification
function showConnectionError(message) {
    // Toast notification or banner
    const banner = document.createElement('div');
    banner.className = 'error-banner';
    banner.textContent = message;
    document.body.appendChild(banner);
}
```

### Tasks:
- [ ] Add structured logging configuration
- [ ] Wrap all websocket operations in try/catch
- [ ] Return success/failure indicators
- [ ] Log errors with context and stack traces
- [ ] Handle specific exceptions (JSONDecodeError, ConnectionClosed)
- [ ] Implement client-side error UI (banner/toast)
- [ ] Add fallback mechanism (retry or long polling)
- [ ] Test various error scenarios
- [ ] Avoid tight error loops

---

## Step 10: Application Lifecycle & Graceful Shutdown (1 hour)
**Concepts:** Startup/shutdown, lifespan events, resource management

### What You'll Build:
- Lifespan context manager
- Start background tasks on startup
- Cleanup on shutdown
- Graceful shutdown

### Key Learning:
- `@asynccontextmanager` decorator
- FastAPI lifespan events
- Resource initialization/cleanup
- Background task management

### Exercise:
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await manager.start_background_tasks()
    logger.info("Application started")

    yield

    # Shutdown
    for client_id in list(manager.active_connections.keys()):
        await manager.disconnect(client_id)
    logger.info("Application stopped")

app = FastAPI(lifespan=lifespan)
```

### Tasks:
- [ ] Create lifespan context manager
- [ ] Start background tasks on startup
- [ ] Disconnect all clients on shutdown
- [ ] Test graceful shutdown (Ctrl+C)
- [ ] Add cleanup for background tasks

---

## Step 11: Security Fundamentals (2 hours)
**Concepts:** Authentication, authorization, origin validation, input validation

### What You'll Build:
- Token-based authentication
- Origin header validation
- Per-message authorization
- Input validation and sanitization
- Connection limits per IP

### Key Learning:
- JWT token validation
- CORS and origin checking
- CSRF protection for WebSockets
- XSS prevention
- DDoS mitigation strategies

### Exercise:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Validate JWT token"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

def validate_origin(origin: Optional[str], allowed_origins: List[str]) -> bool:
    """Validate Origin header to prevent CSRF"""
    if not origin:
        return False  # Reject if no origin (or allow for non-browser clients)
    return origin in allowed_origins

class ConnectionManager:
    def __init__(self):
        self.connections_per_ip: Dict[str, int] = {}
        self.max_connections_per_ip = 10

    async def connect(self, websocket: WebSocket, client_id: str, token: str = None):
        # Validate token
        if not token:
            await websocket.close(code=1008, reason="Authentication required")
            raise HTTPException(status_code=401, detail="No token provided")

        # Validate origin
        origin = websocket.headers.get("origin")
        if not validate_origin(origin, ALLOWED_ORIGINS):
            await websocket.close(code=1008, reason="Invalid origin")
            raise HTTPException(status_code=403, detail="Invalid origin")

        # Check IP connection limit
        client_ip = websocket.client.host
        if self.connections_per_ip.get(client_ip, 0) >= self.max_connections_per_ip:
            await websocket.close(code=1008, reason="Too many connections")
            raise HTTPException(status_code=429, detail="Too many connections")

        await websocket.accept()
        # ... continue connection setup

    def validate_message(self, message: dict, user_id: str) -> bool:
        """Validate and authorize each message"""
        # Check message size
        if len(str(message)) > MAX_MESSAGE_SIZE:
            return False

        # Validate message structure
        if not isinstance(message, dict):
            return False

        # Check authorization for specific actions
        action = message.get("type")
        if action == "admin_broadcast" and user_id not in ADMIN_USERS:
            return False

        # Sanitize input (prevent XSS)
        if "data" in message and isinstance(message["data"], str):
            message["data"] = html.escape(message["data"])

        return True
```

### Tasks:
- [ ] Implement JWT token validation
- [ ] Add Origin header validation
- [ ] Create per-message authorization checks
- [ ] Add message size limits
- [ ] Implement IP-based connection limiting
- [ ] Sanitize all user input (prevent XSS)
- [ ] Add allowed origins whitelist
- [ ] Test with invalid tokens
- [ ] Test CSRF scenarios
- [ ] Rate limit connection attempts per IP

---

## Step 12: Statistics & Monitoring (1.5 hours)
**Concepts:** Metrics, health checks, debugging endpoints, observability

### What You'll Build:
- Connection statistics endpoint
- Health check endpoint
- Real-time metrics tracking
- Error rate monitoring
- Latency tracking
- Admin dashboard

### Key Learning:
- REST endpoints for WebSocket state
- Metrics collection patterns
- Health check best practices
- Debugging production issues
- Performance monitoring

### Exercise:
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Metrics:
    total_connections: int = 0
    total_messages: int = 0
    total_errors: int = 0
    reconnection_count: int = 0
    avg_latency_ms: float = 0.0

class ConnectionManager:
    def __init__(self):
        self.metrics = Metrics()
        self.connection_history: List[dict] = []
        self.error_log: List[dict] = []

    def track_connection(self, client_id: str, event: str):
        """Track connection events for analytics"""
        self.connection_history.append({
            "client_id": client_id,
            "event": event,
            "timestamp": datetime.utcnow().isoformat()
        })
        if event == "connected":
            self.metrics.total_connections += 1
        elif event == "reconnected":
            self.metrics.reconnection_count += 1

    def track_error(self, client_id: str, error: str):
        """Track errors for monitoring"""
        self.error_log.append({
            "client_id": client_id,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.metrics.total_errors += 1

@app.get("/stats")
async def get_stats():
    return {
        "total_connections": len(manager.active_connections),
        "total_rooms": len(manager.room_connections),
        "metrics": {
            "total_messages": manager.metrics.total_messages,
            "total_errors": manager.metrics.total_errors,
            "reconnections": manager.metrics.reconnection_count,
            "avg_latency_ms": manager.metrics.avg_latency_ms
        },
        "room_details": {
            room_id: len(clients)
            for room_id, clients in manager.room_connections.items()
        },
        "recent_errors": manager.error_log[-10:]  # Last 10 errors
    }

@app.get("/health")
async def health_check():
    is_healthy = len(manager.active_connections) < MAX_CONNECTIONS
    return {
        "status": "healthy" if is_healthy else "degraded",
        "connections": len(manager.active_connections),
        "uptime": (datetime.utcnow() - START_TIME).total_seconds()
    }

@app.get("/metrics/prometheus")
async def prometheus_metrics():
    """Prometheus-compatible metrics"""
    return f"""
# HELP websocket_connections Current WebSocket connections
# TYPE websocket_connections gauge
websocket_connections {len(manager.active_connections)}

# HELP websocket_messages_total Total messages sent
# TYPE websocket_messages_total counter
websocket_messages_total {manager.metrics.total_messages}

# HELP websocket_errors_total Total errors
# TYPE websocket_errors_total counter
websocket_errors_total {manager.metrics.total_errors}
"""
```

### Tasks:
- [ ] Implement comprehensive stats endpoint
- [ ] Add health check endpoint with degradation detection
- [ ] Track message counts, error rates, reconnections
- [ ] Add connection duration and latency tracking
- [ ] Implement error logging with retention
- [ ] Create Prometheus-compatible metrics endpoint
- [ ] Build simple admin dashboard (HTML)
- [ ] Add per-room statistics
- [ ] Monitor connection/disconnection rate

---

## Step 13: SSL/TLS & Production Deployment (1.5 hours)
**Concepts:** Secure WebSockets (WSS), HTTPS, production server setup

### What You'll Build:
- WSS (WebSocket Secure) configuration
- SSL/TLS certificate setup
- NGINX reverse proxy configuration
- Production deployment guide

### Key Learning:
- wss:// vs ws:// protocol
- SSL/TLS encryption
- NGINX proxy configuration
- Load balancer considerations
- Certificate management

### Exercise:
```python
# Production server with SSL
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="/path/to/private.key",
        ssl_certfile="/path/to/certificate.crt",
        ws_ping_interval=20,
        ws_ping_timeout=20
    )
```

```nginx
# NGINX configuration for WebSocket
upstream websocket_backend {
    server localhost:8000;
    server localhost:8001;  # Multiple instances
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location /ws {
        proxy_pass http://websocket_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }
}
```

### Tasks:
- [ ] Generate SSL certificates (Let's Encrypt)
- [ ] Configure uvicorn with SSL
- [ ] Set up NGINX reverse proxy
- [ ] Configure WebSocket-specific headers
- [ ] Test wss:// connections
- [ ] Set appropriate timeouts
- [ ] Configure load balancing (if multiple instances)
- [ ] Test with production domain

---

## Step 14: Message Acknowledgment & Reliability (1.5 hours)
**Concepts:** ACK/NACK, delivery guarantees, message queuing

### What You'll Build:
- Message acknowledgment system
- Retry logic for failed messages
- Message queue for offline users
- Delivery confirmation

### Key Learning:
- ACK/NACK pattern
- At-least-once delivery
- Message persistence
- Queue management

### Exercise:
```python
class MessageQueue:
    def __init__(self):
        self.pending_messages: Dict[str, List[dict]] = {}
        self.ack_timeouts: Dict[str, datetime] = {}

    async def send_with_ack(
        self,
        client_id: str,
        message: WSMessage,
        timeout: int = 5
    ) -> bool:
        """Send message and wait for acknowledgment"""
        message.message_id = str(uuid.uuid4())

        # Send message
        await self.send_message(client_id, message)

        # Store for potential retry
        if client_id not in self.pending_messages:
            self.pending_messages[client_id] = []
        self.pending_messages[client_id].append({
            "message": message,
            "sent_at": datetime.utcnow(),
            "retries": 0
        })

        self.ack_timeouts[message.message_id] = datetime.utcnow() + timedelta(seconds=timeout)
        return True

    async def handle_ack(self, client_id: str, message_id: str):
        """Process acknowledgment from client"""
        if client_id in self.pending_messages:
            self.pending_messages[client_id] = [
                m for m in self.pending_messages[client_id]
                if m["message"].message_id != message_id
            ]
        if message_id in self.ack_timeouts:
            del self.ack_timeouts[message_id]

    async def retry_unacked_messages(self):
        """Background task to retry unacknowledged messages"""
        while True:
            await asyncio.sleep(1)
            now = datetime.utcnow()

            for client_id, messages in list(self.pending_messages.items()):
                for msg_info in messages:
                    msg_id = msg_info["message"].message_id
                    if msg_id in self.ack_timeouts and now > self.ack_timeouts[msg_id]:
                        # Timeout reached, retry
                        if msg_info["retries"] < MAX_RETRIES:
                            await self.send_message(client_id, msg_info["message"])
                            msg_info["retries"] += 1
                            self.ack_timeouts[msg_id] = now + timedelta(seconds=5)
                        else:
                            # Max retries reached, give up
                            logger.error(f"Failed to deliver message {msg_id} to {client_id}")
                            self.pending_messages[client_id].remove(msg_info)

# Client-side ACK
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.message_id) {
        // Send acknowledgment
        ws.send(JSON.stringify({
            type: 'ack',
            message_id: data.message_id
        }));
    }
};
```

### Tasks:
- [ ] Implement message ID generation
- [ ] Create ACK message type
- [ ] Build message queue for pending messages
- [ ] Add timeout tracking for ACKs
- [ ] Implement retry logic with max attempts
- [ ] Store messages for offline users
- [ ] Send queued messages on reconnect
- [ ] Test delivery guarantees
- [ ] Handle NACK (negative acknowledgment)

---

## Step 15: Async Best Practices & Performance (1.5 hours)
**Concepts:** AsyncIO patterns, concurrency, backpressure, resource management

### What You'll Build:
- Proper async/await usage
- Concurrent connection handling
- Backpressure management
- Resource pooling
- Performance optimization

### Key Learning:
- Event loop best practices
- asyncio.gather vs asyncio.create_task
- Semaphores and locks
- Backpressure detection
- Memory management

### Exercise:
```python
import asyncio
from asyncio import Semaphore

class ConnectionManager:
    def __init__(self):
        self.send_semaphore = Semaphore(100)  # Limit concurrent sends
        self.broadcast_lock = asyncio.Lock()

    async def send_message_safe(self, conn_info: ConnectionInfo, message: WSMessage):
        """Send with backpressure control"""
        async with self.send_semaphore:
            # Check buffer size (backpressure)
            if hasattr(conn_info.websocket, 'transport'):
                write_buffer_size = conn_info.websocket.transport.get_write_buffer_size()
                if write_buffer_size > MAX_BUFFER_SIZE:
                    logger.warning(f"Backpressure detected for {conn_info.client_id}")
                    await asyncio.sleep(0.1)  # Brief pause

            try:
                await conn_info.websocket.send_json(message.dict())
            except Exception as e:
                logger.error(f"Send error: {e}")

    async def broadcast_optimized(self, message: str, room_id: Optional[str] = None):
        """Optimized broadcast with batching"""
        async with self.broadcast_lock:
            target_clients = self._get_target_clients(room_id)

            # Batch sends for better performance
            batch_size = 50
            for i in range(0, len(target_clients), batch_size):
                batch = target_clients[i:i + batch_size]
                tasks = [
                    self.send_message_safe(self.active_connections[cid], message)
                    for cid in batch if cid in self.active_connections
                ]
                # Don't block on failures
                await asyncio.gather(*tasks, return_exceptions=True)

    async def connection_handler(self, websocket: WebSocket, client_id: str):
        """Proper async connection handling"""
        conn_info = None
        try:
            conn_info = await self.connect(websocket, client_id)

            # Use async for to receive messages
            async for data in websocket.iter_text():
                # Process in background to avoid blocking receives
                asyncio.create_task(self.process_message(conn_info, data))

        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected")
        finally:
            if conn_info:
                await self.disconnect(client_id, conn_info.session_id)
```

### Tasks:
- [ ] Use semaphores to limit concurrent operations
- [ ] Implement backpressure detection
- [ ] Optimize broadcast with batching
- [ ] Use asyncio.gather for parallel operations
- [ ] Avoid blocking the event loop
- [ ] Proper exception handling in async code
- [ ] Use async for with websocket.iter_text()
- [ ] Monitor memory usage
- [ ] Profile async performance

---

## Step 16: Horizontal Scaling with Redis (2+ hours)
**Concepts:** Multi-instance deployment, Redis pub/sub, distributed state

### What You'll Build:
- Redis pub/sub for cross-instance messaging
- Distributed connection tracking
- Sticky sessions (optional)
- Load balancer configuration

### Key Learning:
- Redis pub/sub pattern
- Distributed systems challenges
- Cross-instance communication
- Session affinity
- FastAPI with Redis integration

### Exercise:
```python
import aioredis
from aioredis import Redis

class DistributedConnectionManager:
    def __init__(self):
        self.redis: Optional[Redis] = None
        self.pubsub = None
        self.instance_id = str(uuid.uuid4())
        self.local_connections: Dict[str, ConnectionInfo] = {}

    async def initialize_redis(self):
        """Connect to Redis"""
        self.redis = await aioredis.from_url(
            "redis://localhost",
            encoding="utf-8",
            decode_responses=True
        )
        self.pubsub = self.redis.pubsub()
        await self.pubsub.subscribe("websocket_messages")

        # Start Redis listener
        asyncio.create_task(self.redis_listener())

    async def redis_listener(self):
        """Listen for messages from other instances"""
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])

                # Ignore messages from this instance
                if data.get("instance_id") == self.instance_id:
                    continue

                # Broadcast to local connections
                target_client = data.get("target_client")
                if target_client and target_client in self.local_connections:
                    await self.send_to_local(target_client, data["message"])

    async def broadcast_distributed(
        self,
        message: str,
        room_id: Optional[str] = None
    ):
        """Broadcast across all instances via Redis"""
        # Publish to Redis
        await self.redis.publish(
            "websocket_messages",
            json.dumps({
                "instance_id": self.instance_id,
                "room_id": room_id,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            })
        )

        # Also send to local connections
        await self.broadcast_local(message, room_id)

    async def track_connection_distributed(self, client_id: str, room_id: str):
        """Track connection in Redis"""
        key = f"connection:{client_id}"
        await self.redis.setex(
            key,
            3600,  # 1 hour TTL
            json.dumps({
                "instance_id": self.instance_id,
                "room_id": room_id,
                "connected_at": datetime.utcnow().isoformat()
            })
        )

    async def get_total_connections(self) -> int:
        """Get total connections across all instances"""
        keys = await self.redis.keys("connection:*")
        return len(keys)
```

```nginx
# NGINX with sticky sessions (optional)
upstream websocket_backend {
    ip_hash;  # Sticky sessions based on IP
    server backend1:8000;
    server backend2:8000;
}
```

### Tasks:
- [ ] Install and configure Redis
- [ ] Implement Redis pub/sub client
- [ ] Create distributed broadcast function
- [ ] Track connections in Redis with TTL
- [ ] Listen to Redis messages in background task
- [ ] Test with multiple server instances
- [ ] Configure load balancer (NGINX/HAProxy)
- [ ] Implement sticky sessions (optional)
- [ ] Handle Redis connection failures
- [ ] Monitor cross-instance latency

---

## Step 17: Advanced Production Features (2+ hours)
**Concepts:** Production hardening, persistence, advanced patterns

### What You'll Build:
- Message persistence (database)
- Session recovery
- Circuit breaker pattern
- Advanced monitoring
- Load testing

### Key Learning:
- Database integration
- State recovery
- Resilience patterns
- Performance testing
- Production checklist

### Advanced Topics:
- [ ] Add PostgreSQL/MongoDB for message persistence
- [ ] Implement session state recovery
- [ ] Add circuit breaker for external services
- [ ] Implement message deduplication
- [ ] Add distributed tracing (OpenTelemetry)
- [ ] Load test with Locust or k6
- [ ] Implement graceful degradation
- [ ] Add feature flags
- [ ] Implement A/B testing infrastructure
- [ ] Create deployment automation

---

## 🎯 Final Project Ideas

Once you've completed all steps, try building:

1. **Real-time Chat Application**
   - Multiple rooms
   - Private messages
   - User presence
   - Typing indicators

2. **Live Dashboard**
   - Real-time metrics
   - Live charts
   - Alert system
   - Server monitoring

3. **Collaborative Editor**
   - Multiple users editing
   - Conflict resolution
   - Cursor positions
   - Change history

4. **Multiplayer Game**
   - Game state synchronization
   - Player actions
   - Leaderboards
   - Matchmaking

---

## 📖 Resources

### Official Documentation:
- [FastAPI WebSocket Docs](https://fastapi.tiangolo.com/advanced/websockets/)
- [Python AsyncIO](https://docs.python.org/3/library/asyncio.html)
- [WebSocket Protocol RFC 6455](https://tools.ietf.org/html/rfc6455)
- [WebSocket API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Uvicorn Deployment](https://www.uvicorn.org/deployment/)

### Security Resources:
- [OWASP WebSocket Security](https://owasp.org/www-community/vulnerabilities/WebSocket_security)
- [WebSocket Close Codes](https://websocket.org/reference/close-codes/)
- [JWT Authentication](https://jwt.io/)

### Scaling & Performance:
- [Redis Pub/Sub](https://redis.io/topics/pubsub)
- [NGINX WebSocket Proxy](https://nginx.org/en/docs/http/websocket.html)
- [Load Balancing WebSockets](https://www.nginx.com/blog/websocket-nginx/)

### Testing Tools:
- **Browser DevTools** - Network → WS tab for inspecting frames
- **[websocat](https://github.com/vi/websocat)** - CLI WebSocket client for testing
- **[Postman](https://www.postman.com/)** - GUI tool with WebSocket support
- **[wscat](https://github.com/websockets/wscat)** - Node.js WebSocket client
- **[Locust](https://locust.io/)** - Load testing tool
- **[k6](https://k6.io/)** - Modern load testing tool

### Libraries & Tools:
- **[python-socketio](https://python-socketio.readthedocs.io/)** - Socket.IO for Python
- **[encode/broadcaster](https://github.com/encode/broadcaster)** - Broadcast channel for WebSockets
- **[aioredis](https://aioredis.readthedocs.io/)** - Async Redis client
- **[prometheus-client](https://github.com/prometheus/client_python)** - Metrics collection

### Debugging Tips:
- Use `logger.debug()` liberally with context (client_id, session_id)
- Check browser console for client-side errors
- Monitor Network tab for WebSocket frames and close codes
- Use `exc_info=True` in logging for stack traces
- Test with multiple browser tabs to simulate concurrent connections
- Use Redis CLI to monitor pub/sub messages
- Profile with `py-spy` or `cProfile` for performance issues

---

## 💡 Learning Tips

1. **Build incrementally** - Don't skip steps
2. **Break things intentionally** - See how errors are handled
3. **Read the logs** - Understand the flow
4. **Test edge cases** - Multiple tabs, slow connections, rapid reconnects
5. **Refactor as you go** - Keep code clean
6. **Ask questions** - Why does this pattern exist?

---

## ✅ Completion Checklist

After finishing all steps, you should understand:

### Core Concepts:
- [ ] How WebSockets differ from HTTP
- [ ] Connection lifecycle management (connect, disconnect, reconnect)
- [ ] Real-time bidirectional communication
- [ ] Concurrent connection handling with asyncio
- [ ] Event loop and async/await patterns

### Production Features:
- [ ] Heartbeat and connection health monitoring
- [ ] Rate limiting and DDoS prevention
- [ ] Graceful reconnection with exponential backoff
- [ ] Session management and race condition prevention
- [ ] Proper WebSocket close codes
- [ ] Error handling and recovery strategies

### Security:
- [ ] JWT/Token authentication
- [ ] Origin validation (CSRF protection)
- [ ] Per-message authorization
- [ ] Input validation and XSS prevention
- [ ] Connection limits per IP
- [ ] SSL/TLS (WSS) configuration

### Scalability:
- [ ] Redis pub/sub for multi-instance
- [ ] Load balancer configuration
- [ ] Sticky sessions (when needed)
- [ ] Distributed connection tracking
- [ ] Horizontal scaling patterns

### Reliability:
- [ ] Message acknowledgment (ACK/NACK)
- [ ] Message queuing for offline users
- [ ] Delivery guarantees
- [ ] Circuit breaker patterns
- [ ] Graceful shutdown

### Observability:
- [ ] Metrics collection (connections, messages, errors)
- [ ] Health check endpoints
- [ ] Structured logging
- [ ] Performance monitoring
- [ ] Error tracking

---

## 🚀 Production Readiness Checklist

Before deploying to production, ensure:

### Infrastructure:
- [ ] SSL/TLS certificates configured (Let's Encrypt)
- [ ] NGINX/HAProxy reverse proxy setup
- [ ] Proper timeouts configured (proxy, WebSocket, application)
- [ ] Multiple server instances for redundancy
- [ ] Redis cluster for distributed state
- [ ] Database for message persistence (if needed)

### Security:
- [ ] All WebSocket connections use WSS (not WS)
- [ ] Authentication on connection handshake
- [ ] Authorization on per-message basis
- [ ] Origin header validation
- [ ] Rate limiting on connections and messages
- [ ] Input sanitization for all user data
- [ ] Secrets stored in environment variables

### Monitoring:
- [ ] Metrics endpoint (/metrics, /stats)
- [ ] Health check endpoint (/health)
- [ ] Prometheus/Grafana integration
- [ ] Error tracking (Sentry, etc.)
- [ ] Log aggregation (ELK, Datadog, etc.)
- [ ] Alerts for high error rates, connection spikes

### Performance:
- [ ] Load tested with expected traffic (Locust, k6)
- [ ] Backpressure handling implemented
- [ ] Connection pooling configured
- [ ] Message batching for broadcasts
- [ ] Memory leaks checked and fixed
- [ ] CPU profiling done

### Reliability:
- [ ] Graceful shutdown on SIGTERM
- [ ] All clients notified on shutdown
- [ ] Background tasks properly cleaned up
- [ ] Message delivery guarantees tested
- [ ] Reconnection logic tested thoroughly
- [ ] Chaos testing performed

### Documentation:
- [ ] API documentation (connection flow, message types)
- [ ] Deployment guide
- [ ] Runbook for common issues
- [ ] Architecture diagrams
- [ ] Security best practices documented

### Testing:
- [ ] Unit tests for core logic
- [ ] Integration tests for WebSocket endpoints
- [ ] Load tests passing
- [ ] Security tests (penetration testing)
- [ ] Chaos testing (network failures, server crashes)
- [ ] Client reconnection scenarios tested

---

## 🎓 Estimated Total Learning Time

- **Beginner Path (Steps 1-7):** ~10-12 hours
- **Intermediate Path (Steps 8-12):** ~8-10 hours
- **Advanced Path (Steps 13-17):** ~12-15 hours
- **Total:** ~30-37 hours of hands-on learning

**Recommendation:** Spend 1-2 weeks going through all steps, building incrementally. Don't rush—understanding is more important than speed!

---

## Next Steps

After completing this learning plan:

1. **Review Production Code**
   - Study `main.py` in detail
   - Understand each design decision
   - Identify patterns used

2. **Build Your Own Project**
   - Start with a simple use case
   - Add features incrementally
   - Apply all learned concepts

3. **Deploy to Production**
   - Use a cloud provider (AWS, GCP, Azure)
   - Set up monitoring and alerts
   - Document your deployment

4. **Continue Learning**
   - Explore WebRTC for media streaming
   - Learn about MQTT for IoT
   - Study gRPC streaming
   - Investigate Server-Sent Events (SSE)

5. **Contribute Back**
   - Share your learnings
   - Contribute to open source
   - Write blog posts
   - Help others learn

---

## 📚 Additional Topics (Beyond This Plan)

If you want to dive deeper:

- **WebRTC** - Peer-to-peer communication
- **Server-Sent Events (SSE)** - One-way push from server
- **gRPC Streaming** - Bi-directional RPC streams
- **MQTT** - IoT messaging protocol
- **GraphQL Subscriptions** - Real-time GraphQL
- **Socket.IO** - Higher-level abstraction over WebSocket
- **WebSocket Compression** - Permessage-deflate extension
- **Binary Protocols** - Protocol Buffers, MessagePack
- **Cloud-Native Solutions** - AWS API Gateway WebSocket, Pusher, Ably

---

**Happy learning! 🚀**

Remember: Production WebSocket development is complex, but you're building the skills step-by-step. Each concept builds on the last, and by the end, you'll have a comprehensive understanding of real-time communication at scale.

**Questions? Issues? Found a bug in the learning plan?** Open an issue or contribute improvements!
