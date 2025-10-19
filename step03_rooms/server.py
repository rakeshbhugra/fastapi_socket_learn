from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.room_connections: dict[str, set[str]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        room_id: str,
    ):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        if room_id not in self.room_connections:
            self.room_connections[room_id] = set()
        self.room_connections[room_id].add(client_id)

    async def broadcast_to_room(self, room_id: str, message: str):
        if room_id in self.room_connections:
            for client_id in self.room_connections[room_id]:
                connection = self.active_connections.get(client_id)
                if connection:
                    try:
                        await connection.send_text(message)
                    except Exception:
                        # Connection broken, will be cleaned up on disconnect
                        pass

    def disconnect(self, client_id: str, room_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if room_id in self.room_connections:
            self.room_connections[room_id].discard(client_id)


manager = ConnectionManager()


@app.websocket("/ws/{room_id}/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    client_id: str,
):
    await manager.connect(websocket, client_id, room_id)
    await manager.broadcast_to_room(room_id, f"{client_id} joined the room {room_id}")

    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast_to_room(room_id, f"{client_id}: {data}")

    except WebSocketDisconnect:
        manager.disconnect(client_id, room_id)
        await manager.broadcast_to_room(room_id, f"{client_id} left the room {room_id}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
