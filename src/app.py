from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from src.modules.websocket.manager import ConnectionManager


app = FastAPI()
connection_manager = ConnectionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            print(data)
            response = {
                "message": f"Hello, {user_id}! Message received.",
            }
            await websocket.send_json(response)
    except WebSocketDisconnect:
        print(f"Client disconnected: {user_id}")