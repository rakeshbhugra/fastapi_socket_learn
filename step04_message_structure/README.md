# Step 4: Message Structure & Types

Learn JSON messages, Pydantic validation, and message types.

## Your Tasks

### Server (server.py)

#### 1. Define MessageType Enum (Line 18)
```python
class MessageType(str, Enum):
    MESSAGE = "message"
    BROADCAST = "broadcast"
    ERROR = "error"
    SYSTEM = "system"
```

#### 2. Create WSMessage Model (Line 22-34)
```python
class WSMessage(BaseModel):
    type: MessageType
    data: Any
    timestamp: datetime = datetime.utcnow()
    message_id: Optional[str] = None
    sender: Optional[str] = None
```

#### 3. Implement `send_message()` (Line 49)
- Get the websocket from `self.active_connections[client_id]`
- Use `await connection.send_json(message.model_dump())`
- Add try/except for error handling

#### 4. Implement `broadcast_to_room()` (Line 60)
- Loop through `self.room_connections[room_id]`
- Call `self.send_message()` for each client_id
- Handle exceptions

#### 5. Implement WebSocket Endpoint Logic (Lines 87-110)
- Receive JSON: `data = await websocket.receive_json()`
- Create WSMessage: `msg = WSMessage(**data)`
- Add message_id: `msg.message_id = str(uuid4())`
- Broadcast to room
- Handle validation errors with try/except

### Client (client.html)

#### 1. Complete MessageType Object (Line 97)
Add BROADCAST, ERROR, SYSTEM

#### 2. Implement `addMessage()` (Line 100)
- Create div with class based on message type
- Display message.data
- Show metadata (timestamp, sender, message_id)
- Append and scroll

#### 3. Implement `ws.onmessage()` (Line 131)
- Parse JSON: `const msg = JSON.parse(event.data)`
- Call `addMessage(msg)`
- Handle errors

#### 4. Implement `sendMessage()` (Line 155)
- Create message object with type, data, sender, timestamp
- Send: `ws.send(JSON.stringify(messageObj))`
- Clear input

## Testing

1. Fill in all TODOs
2. Run: `python server.py`
3. Open `client.html` in browser
4. Check that messages now show:
   - Different colors for different types
   - Timestamps
   - Message IDs
   - Sender names

## What You're Learning

- **JSON vs Text**: Structured data instead of plain strings
- **Pydantic Validation**: Automatic type checking and validation
- **Message Types**: Different categories of messages
- **Metadata**: Timestamps and unique IDs for tracking
- **send_json/receive_json**: WebSocket JSON methods

Good luck! 🚀
