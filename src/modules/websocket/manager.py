from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        pass

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

    async def disconnect(self, websocket: WebSocket):
        await websocket.close()

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)