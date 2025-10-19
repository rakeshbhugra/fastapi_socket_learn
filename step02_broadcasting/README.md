# Step 2: Broadcasting Chat

Simple increment from Step 1 - now supports multiple clients and broadcasting.

## What's New

- **ConnectionManager class**: Tracks all active connections
- **Broadcasting**: Messages sent to all connected clients
- **Client ID**: Each client has a unique name from URL path
- **Join/Leave notifications**: Everyone sees when users connect/disconnect

## Key Concepts

```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
```

Simple list to track all connections. Later steps will make this more sophisticated.

## How to Test

1. Start the server:
```bash
python server.py
```

2. Open `client.html` in **multiple browser tabs** (or different browsers)

3. Give each tab a different name (User1, User2, etc.)

4. Connect all tabs

5. Send messages from any tab - **all tabs will receive it!**

## What You'll See

- When you connect: "User1 joined the chat" appears in all tabs
- When you send a message: "User1: hello" appears in all tabs
- When you disconnect: "User1 left the chat" appears in remaining tabs

## Next Step

Step 3 will add **rooms** so users can join different channels!
