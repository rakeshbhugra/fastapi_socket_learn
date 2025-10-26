# Production WebSocket Chat - Implementation Plan
## AI Dating App: Real-time Chat with AI Matches

This is your working plan. Update checkboxes as you decide what to include/exclude.

---

## 💡 Architecture Overview

**Key Architectural Decisions:**
1. **Rooms = Conversations** (1-to-1 with AI)
2. **Multi-Device Support** (one user, multiple websockets)
3. **ACK/NACK Pattern** (message reliability with user-controlled retries) ⭐

### Conversations (Rooms)
- Each conversation with an AI match is a separate "room"
- `room_id` = `conversation_id` (e.g., "conv_user123_ai_alex")
- One user per conversation, but supports **multiple devices**
- User can have multiple conversations with different AI matches
- Messages isolated per conversation

### Multi-Device Support
- Same user connects from iPhone, iPad, web browser
- All devices join the same conversation room
- Messages/AI responses delivered to all user's devices
- Typing indicators synced across devices
- Connection tracking: `Dict[str, List[WebSocket]]`

### ACK/NACK Reliability Pattern ⭐
**Why we chose ACK/NACK:**
- ✅ **No DLQ needed** - Backend doesn't manage retry queues
- ✅ **Simpler state** - Frontend tracks: sending/delivered/failed (3 states)
- ✅ **User control** - User decides when to retry failed messages
- ✅ **Clear feedback** - Immediate error notification on NACK
- ✅ **DB confirmation** - ACK confirms message saved to database
- ✅ **Easier debugging** - Clear success/failure signals

**Message Flow:**
```
User sends → Backend validates → Backend saves to DB → Backend broadcasts
           ↓                   ↓                      ↓
        If fail: NACK      If success: ACK      All devices get message
           ↓                   ↓
    User sees error      User sees delivered
    User can retry       Message confirmed
```

---

## 🎯 Core Requirements (Must Have)

### Connection Management
- [ ] ConnectionManager class with proper state tracking
- [ ] User ID management (unique per user)
- [ ] Conversation support (room_id = conversation_id)
- [ ] Track active connections: `Dict[str, List[WebSocket]]` (user → websockets for multi-device)
- [ ] Track conversation connections: `Dict[str, Set[str]]` (conversation_id → user_ids)
- [ ] Handle multiple devices per user (same user_id, different websockets)

### Message Structure
- [ ] Pydantic models for all messages
- [ ] Message types enum (CHAT_MESSAGE, AI_RESPONSE, ACK, NACK, SYSTEM, ERROR, TYPING, etc.)
- [ ] Structured message format with:
  - [ ] type: MessageType
  - [ ] message_id: unique ID (UUID) - **required for ACK/NACK**
  - [ ] conversation_id: conversation ID
  - [ ] data: payload
  - [ ] timestamp: datetime
  - [ ] sender: client_id (optional)
- [ ] JSON send/receive (send_json, receive_json)

### ACK/NACK Pattern (Message Reliability)
- [ ] ACK message type - confirms successful processing
- [ ] NACK message type - indicates processing failure
- [ ] Send ACK when:
  - [ ] Message validated successfully
  - [ ] Message saved to database
  - [ ] Message broadcast completed
- [ ] Send NACK when:
  - [ ] Validation fails (invalid format, missing fields)
  - [ ] Database operation fails
  - [ ] Authorization fails (user not in conversation)
  - [ ] Rate limit exceeded
  - [ ] Any business logic error
- [ ] Include error details in NACK data field
- [ ] Frontend promise-based ACK handling
- [ ] Timeout handling (10 seconds default)
- [ ] Message status tracking: sending → delivered/failed

**Why ACK/NACK:**
- ✅ Simpler backend (no DLQ/retry logic needed)
- ✅ Clearer frontend state management (3 states vs 4+)
- ✅ User-controlled retries (better UX)
- ✅ Immediate error feedback
- ✅ Database persistence confirmation
- ✅ Easier debugging and monitoring

### Reliability & Health
- [ ] Heartbeat mechanism (server → client ping, client → server pong)
- [ ] Heartbeat interval: configurable (default 30s)
- [ ] Heartbeat timeout: configurable (default 60s)
- [ ] Detect and close stale connections
- [ ] Background task for heartbeat monitoring
- [ ] Track last_heartbeat timestamp per connection

### Reconnection & Recovery
- [ ] Session ID tracking (different from connection)
- [ ] Detect reconnection (same client_id reconnects)
- [ ] Gracefully close old connection before accepting new
- [ ] Handle race conditions on reconnect
- [ ] Increment reconnection counter
- [ ] Client-side exponential backoff with jitter
- [ ] Max reconnection attempts (configurable)

### Error Handling
- [ ] Try/catch around all WebSocket operations
- [ ] Graceful handling of:
  - [ ] WebSocketDisconnect
  - [ ] JSONDecodeError (invalid message format)
  - [ ] ValidationError (Pydantic validation failure)
  - [ ] Connection send failures
- [ ] Send error messages to client on validation failure
- [ ] Logging with proper context (client_id, session_id, error)
- [ ] Don't crash server on single client error

### Graceful Shutdown
- [ ] Lifespan context manager
- [ ] Startup: initialize background tasks
- [ ] Shutdown: disconnect all clients with proper close code
- [ ] Shutdown: cancel background tasks
- [ ] Send GOING_AWAY close code to all clients
- [ ] Allow existing messages to complete before shutdown

### WebSocket Close Codes
- [ ] Enum for standard close codes:
  - [ ] 1000 NORMAL - Normal closure
  - [ ] 1001 GOING_AWAY - Server shutting down
  - [ ] 1002 PROTOCOL_ERROR - Protocol error
  - [ ] 1007 INVALID_DATA - Invalid frame payload
  - [ ] 1008 POLICY_VIOLATION - Policy violation
  - [ ] 1011 INTERNAL_ERROR - Server error
- [ ] Use proper close codes for different scenarios
- [ ] Include reason string in close frames

---

## 📊 Monitoring & Observability (Recommended)

### Statistics & Metrics
- [ ] REST endpoint: GET /stats
- [ ] REST endpoint: GET /health
- [ ] Track metrics:
  - [ ] Total connections (current)
  - [ ] Total messages sent
  - [ ] Total errors
  - [ ] Reconnection count
  - [ ] Message rate
  - [ ] Connection duration
- [ ] Per-room statistics
- [ ] Connection history (last N events)
- [ ] Error log (last N errors with context)

### Logging
- [ ] Structured logging configuration
- [ ] Log levels: INFO for normal, DEBUG for detailed
- [ ] Log connection events (connect, disconnect, reconnect)
- [ ] Log errors with full context and stack traces
- [ ] Log message flow for debugging
- [ ] Use logger.exception() for exceptions

---

## 🚀 Performance & Scalability (Important)

### Async Best Practices
- [ ] Use asyncio.gather for concurrent sends
- [ ] Batch broadcasts (send to N clients at a time)
- [ ] Semaphore to limit concurrent operations
- [ ] Detect backpressure (buffer size)
- [ ] Use async for with websocket.iter_text()
- [ ] Don't block event loop
- [ ] Proper exception handling in async code

### Rate Limiting
- [ ] Per-client message rate limiting
- [ ] Sliding window algorithm
- [ ] Track message timestamps per client
- [ ] Configurable: messages per window
- [ ] Configurable: time window (seconds)
- [ ] Clean up old timestamps
- [ ] Send rate limit error to client

### Connection Limits
- [ ] Max connections per IP (DDoS protection)
- [ ] Max total connections globally
- [ ] Track connections by IP address
- [ ] Reject new connections when limit reached
- [ ] Send appropriate close code and reason

---

## 🔧 Dating App Specific Features

### Message Types for AI Dating App
- [ ] **CHAT_MESSAGE** - Regular chat message from user
- [ ] **AI_RESPONSE** - AI match response (distinguished from user message)
- [ ] **ACK** - Acknowledgment (message processed successfully)
- [ ] **NACK** - Negative acknowledgment (message failed, includes error details)
- [ ] **TYPING_INDICATOR** - AI is "typing" (simulate realistic conversation)
- [ ] **READ_RECEIPT** - Message read by AI (confirmation)
- [ ] **NEW_MATCH** - New AI match created notification
- [ ] **AI_STATUS** - AI match status (online/offline simulation)
- [ ] **CONVERSATION_CREATED** - New conversation with AI match started
- [ ] **SYSTEM** - System messages (maintenance, info)
- [ ] **ERROR** - Error messages (connection issues, etc.)

### Conversation Management (AI Dating Specific)
- [ ] One-on-one conversations: User ↔ AI Match (room_id = conversation_id)
- [ ] Each user can have multiple concurrent AI conversations
- [ ] Track which conversation each connection belongs to
- [ ] Validate user owns conversation before joining
- [ ] Multi-device: Same user, same conversation → all devices get messages
- [ ] Support AI response broadcasting to user's devices
- [ ] Isolate conversations (messages in conv_A don't go to conv_B)

### Presence & Typing (AI Simulation)
- [ ] Track user online status (real)
- [ ] Simulate AI "online" status for realism
- [ ] AI typing indicator with delay (simulate thinking time, 1-3 seconds)
- [ ] User typing indicator (real-time)
- [ ] Typing indicator timeout (stop after 3-5 seconds)
- [ ] Broadcast typing to all user's devices (multi-device sync)

---

## ❌ Explicitly Excluded (You're Handling Separately)

### Database & Persistence
- [ ] ~~Message persistence to database~~ (You handle)
- [ ] ~~Message history retrieval~~ (You handle)
- [ ] ~~Conversation state storage~~ (You handle)
- [ ] ~~User data storage~~ (You handle)
- [ ] ~~Offline message queue~~ (Optional - You decide)

### Security & Authentication
- [ ] ~~JWT token validation~~ (You handle later)
- [ ] ~~Origin header validation~~ (You handle later)
- [ ] ~~Per-message authorization~~ (You handle later)
- [ ] ~~Input sanitization (XSS)~~ (You handle later)
- [ ] ~~Allowed origins whitelist~~ (You handle later)

### Deployment & Infrastructure
- [ ] ~~SSL/TLS configuration~~ (You handle)
- [ ] ~~NGINX reverse proxy~~ (You handle)
- [ ] ~~Redis pub/sub for scaling~~ (You handle if needed)
- [ ] ~~Load balancer config~~ (You handle)
- [ ] ~~Docker/K8s deployment~~ (You handle)

---

## 📁 File Structure

```
main.py                    # Production WebSocket server
├── Models
│   ├── MessageType (Enum)
│   ├── WSMessage (BaseModel)
│   ├── ConnectionInfo (dataclass/BaseModel)
│   └── CloseCode (Enum)
├── ConnectionManager
│   ├── __init__
│   │   • active_connections: Dict[str, List[WebSocket]]  # user_id → websockets
│   │   • conversation_connections: Dict[str, Set[str]]   # conversation_id → user_ids
│   │   • connection_info: Dict[WebSocket, ConnectionInfo]
│   ├── connect(websocket, user_id, conversation_id)
│   │   • Accept connection
│   │   • Add to user's websocket list (multi-device)
│   │   • Add user to conversation room
│   ├── disconnect(websocket, user_id, conversation_id)
│   │   • Remove from user's websocket list
│   │   • Clean up if user has no more devices connected
│   │   • Clean up empty conversations
│   ├── send_to_user(user_id, message)
│   │   • Send to all user's connected devices (asyncio.gather)
│   ├── broadcast_to_conversation(conversation_id, message)
│   │   • Send to all users in conversation (usually just 1)
│   │   • Reaches all devices of that user
│   ├── send_ack(websocket, message_id, data="Success")
│   │   • Send ACK response for successful processing
│   ├── send_nack(websocket, message_id, error_message)
│   │   • Send NACK response with error details
│   ├── check_rate_limit(user_id)
│   ├── heartbeat_monitor() [background task]
│   └── cleanup_stale_connections()
├── WebSocket Endpoints
│   └── /ws/{user_id}?conversation_id={conversation_id}
├── REST Endpoints
│   ├── GET / (health check)
│   ├── GET /stats
│   ├── GET /health
│   └── POST /api/send-ai-message (Your AI service → WebSocket broadcast)
└── Lifespan Management
    ├── startup: start background tasks
    └── shutdown: graceful disconnect all
```

**Key Points:**
- `user_id` in path identifies the user
- `conversation_id` in query identifies which AI conversation
- User can connect multiple times (different devices) to same conversation
- All devices get the same AI responses

---

## 🔄 Typical Flow (AI Dating App)

### User Opens Conversation
```
1. User opens app on iPhone
   → ws.connect('ws://api.com/ws/user_123?conversation_id=conv_user123_ai_alex')

2. User also has iPad open with same conversation
   → ws.connect('ws://api.com/ws/user_123?conversation_id=conv_user123_ai_alex')

3. Both connections in same conversation "room"
   → ConnectionManager tracks 2 websockets for user_123 in conv_user123_ai_alex
```

### User Sends Message (With ACK/NACK)
```
1. User types on iPhone: "Hey Alex!"
   → Frontend shows message as "sending" (grey check)
   → WebSocket sends with message_id: "msg_12345"

2. Backend receives message
   → Validates message
   → Saves to database
   → Broadcasts to conversation (iPhone + iPad get it)
   → Sends ACK back to sender: { type: "ACK", message_id: "msg_12345" }

3. iPhone receives ACK
   → Updates message status to "delivered" (green check)
   → User knows message was processed successfully

4. iPad receives broadcast
   → Shows message from iPhone immediately

---

If database fails:
2b. Backend tries to save → Database error
    → Sends NACK: { type: "NACK", message_id: "msg_12345", data: "DB error" }

3b. iPhone receives NACK
    → Shows message as "failed" (red X)
    → Shows retry button
    → User taps retry → Sends again with new message_id
```

### AI Response Flow
```
1. Your AI service generates response
   → POST /api/send-ai-message
     {
       "conversation_id": "conv_user123_ai_alex",
       "message": "Hi! How's your day?",
       "message_id": "ai_msg_67890"
     }

2. WebSocket server receives
   → Validates conversation exists
   → Broadcasts to conversation
   → Both iPhone and iPad receive AI response instantly
   → Sends ACK back to AI service (confirms delivery initiated)
```

### Multi-Device Sync
```
All devices in same conversation get:
- User's own messages (sent from any device)
- AI responses
- Typing indicators
- Read receipts
- System messages
```

### Complete Message Exchange Example (ACK Success)
```json
// 1. Frontend → Backend (User sends message)
{
  "type": "CHAT_MESSAGE",
  "message_id": "msg_abc123",
  "conversation_id": "conv_user123_ai_alex",
  "data": "Hey Alex, how are you?",
  "sender": "user_123",
  "timestamp": "2025-01-15T10:30:00Z"
}

// 2. Backend validates, saves to DB, broadcasts

// 3. Backend → Frontend (ACK to sender's device)
{
  "type": "ACK",
  "message_id": "msg_abc123",  // Same ID
  "conversation_id": "conv_user123_ai_alex",
  "data": "Message processed successfully",
  "timestamp": "2025-01-15T10:30:00.123Z"
}

// 4. Backend → All devices in conversation (Broadcast)
{
  "type": "CHAT_MESSAGE",
  "message_id": "msg_abc123",
  "conversation_id": "conv_user123_ai_alex",
  "data": "Hey Alex, how are you?",
  "sender": "user_123",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Complete Message Exchange Example (NACK Failure)
```json
// 1. Frontend → Backend (User sends message)
{
  "type": "CHAT_MESSAGE",
  "message_id": "msg_xyz789",
  "conversation_id": "conv_user123_ai_alex",
  "data": "",  // Empty message!
  "sender": "user_123",
  "timestamp": "2025-01-15T10:31:00Z"
}

// 2. Backend validates → Validation fails (empty message)

// 3. Backend → Frontend (NACK to sender)
{
  "type": "NACK",
  "message_id": "msg_xyz789",  // Same ID
  "conversation_id": "conv_user123_ai_alex",
  "data": "Message cannot be empty",  // Error details
  "timestamp": "2025-01-15T10:31:00.050Z"
}

// 4. Frontend receives NACK
//    → Shows error toast: "Message cannot be empty"
//    → Shows retry button
//    → Keeps message text in input
```

### User Switches Conversations
```
User has 3 AI matches:
- Opens conversation with Alex → conversation_id=conv_user123_ai_alex
- Switches to Sam → Disconnects, reconnects with conversation_id=conv_user123_ai_sam
- Messages isolated per conversation
```

---

## 🎯 Implementation Priority

### Phase 1: Core Functionality (MVP)
1. Basic ConnectionManager with dict storage (multi-device support)
2. Message structure with Pydantic (include message_id)
3. Conversation-based broadcasting (room_id = conversation_id)
4. **ACK/NACK implementation** (critical for reliability)
5. Basic error handling (try/except around all operations)
6. WebSocket endpoint with connect/disconnect
7. Frontend promise-based message sending with timeout

### Phase 2: Reliability
1. Heartbeat implementation
2. Reconnection handling
3. Proper close codes
4. Graceful shutdown
5. Comprehensive error handling

### Phase 3: Production Hardening
1. Rate limiting
2. Connection limits
3. Statistics endpoints
4. Async optimizations
5. Logging improvements

### Phase 4: Dating App Features
1. Typing indicators
2. Read receipts
3. Online status
4. Dating-specific message types
5. Presence tracking

---

## 💻 Frontend Implementation (ACK/NACK Pattern)

### Required Components

#### 1. Message State Management
```javascript
Message States:
- 'sending'   → Grey single checkmark (waiting for ACK)
- 'delivered' → Green double checkmark (got ACK)
- 'failed'    → Red X with retry button (got NACK or timeout)
```

#### 2. Promise-Based Sending
```javascript
Features:
- sendMessage() returns Promise
- Promise resolves on ACK
- Promise rejects on NACK or timeout
- Store pending promises in Map<message_id, {resolve, reject}>
```

#### 3. Timeout Handling
```javascript
Configuration:
- Default timeout: 10 seconds
- Clear timeout on ACK/NACK
- Show retry button on timeout
- Keep message text in input on failure
```

#### 4. Retry Mechanism
```javascript
Features:
- Manual retry button for failed messages
- Generate new message_id on retry
- Optional: Auto-retry once on timeout, then show button
- Remove old failed message when retrying
```

#### 5. UI Components
```javascript
Required Elements:
- Message status indicator (checkmarks, X)
- Retry button
- Error toast/banner
- Loading state during send
```

### Frontend Checklist
- [ ] ChatManager class with pendingMessages Map
- [ ] sendMessage() returns Promise
- [ ] sendWithAck() helper function
- [ ] handleACK() message handler
- [ ] handleNACK() message handler
- [ ] Timeout management (10s default)
- [ ] UI status indicators (sending/delivered/failed)
- [ ] Retry button implementation
- [ ] Error toast notifications
- [ ] Keep failed message text for retry
- [ ] Clear input only on successful send

---

## 📝 Notes

- Review this plan and check/uncheck items based on your needs
- Add dating-app specific requirements as needed
- Update priorities based on your timeline
- Keep security placeholders for future integration
- Focus on solid ConnectionManager first - it's the foundation

### ACK/NACK Implementation Notes

**Backend Considerations:**
- Always send ACK/NACK - never leave client hanging
- Include meaningful error messages in NACK data field
- Log all NACK events for monitoring
- Consider rate limiting ACK/NACK messages (shouldn't be needed, but good practice)
- ACK should only be sent AFTER database persistence succeeds
- Use try/except around all business logic to catch errors for NACK

**Frontend Considerations:**
- Set reasonable timeout (10 seconds recommended)
- Clean up pending promises on component unmount
- Show loading state immediately on send
- Don't clear input field until ACK received
- Provide clear retry mechanism
- Consider auto-retry once on timeout, then manual retry
- Store failed messages locally in case user closes app

**Performance:**
- ACK/NACK adds one extra message per user message (~100 bytes)
- For 1000 messages/day: ~100KB extra traffic (negligible)
- Promise overhead is minimal (a few objects in memory)
- Timeout timers are cheap (event loop handles efficiently)

**Trade-offs:**
- ✅ Clearer reliability guarantees
- ✅ Simpler backend (no DLQ)
- ✅ Better UX (immediate feedback)
- ❌ Slightly more complex frontend (promise management)
- ❌ One extra message per user message (tiny overhead)

### Integration with AI Service

**Option 1: AI Service Calls WebSocket Server (Recommended)**
```python
# Your AI service generates response, then:
async with httpx.AsyncClient() as client:
    await client.post('http://websocket-server/api/send-ai-message', json={
        'conversation_id': 'conv_user123_ai_alex',
        'message': ai_response,
        'type': 'AI_RESPONSE'
    })
# WebSocket server broadcasts to all user's devices
```

**Option 2: WebSocket Server Calls AI Service**
```python
# User sends message via WebSocket
# WebSocket server calls AI service:
ai_response = await ai_service.generate_response(message)
# Broadcast AI response back through WebSocket
```

**Recommendation:** Option 1 is more flexible and decouples services.

---

## Next Steps

1. **Review this plan** - Check/uncheck what you need
2. **Prioritize** - Mark what's MVP vs nice-to-have
3. **Confirm architecture** - Multi-device + conversations makes sense?
4. **Ready?** - Tell me when to generate `main.py` with your requirements!

I'll create the production-ready `main.py` based on what you check off! 🚀
