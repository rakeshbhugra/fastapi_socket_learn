import asyncio
import websockets
import json
from datetime import datetime, UTC


async def websocket_client():
    user_id = "test_user"
    conversation_id = "test_conversation"
    port = 3200

    
    ws_url = f"ws://localhost:{port}/ws/{user_id}?conversation_id={conversation_id}"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"Connected to {ws_url}")

            message = {
                "type": "chat_message",  # MessageType.CHAT_MESSAGE
                "message_id": f"msg_test_{int(datetime.now(UTC).timestamp())}",
                "conversation_id": conversation_id,
                "data": "Hello! This is a test message. How are you today?",
                "sender": user_id,
                "timestamp": datetime.now(UTC).isoformat()
            }

            await websocket.send(json.dumps(message))
            print(f"Sent: {message}")

            response = await websocket.recv()
            print(f"Received: {response}")

        
            timeout = 15  # Wait up to 15 seconds for responses
            try:
                while True:
                    response = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=timeout
                    )
                    print(f"Received: {response}")
                    data = json.loads(response)
        
                    print(json.dumps(data, indent=2))

            except asyncio.TimeoutError:
                print(f"No more messages received in {timeout} seconds. Exiting.")

            except Exception as e:
                print(f"An error occurred while receiving messages: {e}")
        
    
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(websocket_client())
