# Step 3: Rooms & Channels

Simple increment from Step 2 - now supports multiple rooms/channels.

## What's New

- **Room-based connections**: Each client joins a specific room
- **Dictionary storage**: Clients stored by ID instead of just a list
- **Room tracking**: `room_connections` dict maps rooms to sets of client IDs
- **Targeted broadcasting**: Messages only go to clients in the same room

## Key Concepts

```python
self.active_connections: dict[str, WebSocket] = {}
self.room_connections: dict[str, set[str]] = {}
```

Now we track:
- Which WebSocket belongs to which client (by ID)
- Which clients are in which rooms

```python
@app.websocket("/ws/{room_id}/{client_id}")
```

URL now has **two path parameters**: room and client name.

## How to Test

1. Start the server:
```bash
python server.py
```

2. Open `client.html` in **multiple browser tabs**

3. Put some tabs in "lobby", others in "general", others in "random"

4. Connect all tabs

5. Send messages - **only tabs in the same room will see them!**

## What You'll See

**Tab 1** (lobby + User1):
- Sees: User1 joined, User2 joined (if User2 also joins lobby)
- Does NOT see: User3's messages if User3 is in "general"

**Tab 2** (general + User3):
- Only sees messages from other people in "general"
- Isolated from "lobby" room

This is the foundation for chat apps, game lobbies, etc.!

## Next Step

Step 4 will add **JSON message structure** with message types and validation!
