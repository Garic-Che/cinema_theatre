import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from service.bearer import decode_token
from connection_manager import ConnectionManager
from core.logger import logger

router = APIRouter()
connection_manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Получение токена из заголовка Authorization
    auth_header = websocket.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        await websocket.close(code=4003, reason="Bearer token required")
        return

    token = auth_header.split(" ")[1]
    user = decode_token(token)
    if not user:
        await websocket.close(code=4003, reason="Invalid or expired token")
        return

    user_id = user.get("user_id")
    if not user_id:
        await websocket.close(code=4003, reason="User ID not found in token")
        return

    await websocket.accept()
    await connection_manager.connect(websocket, user_id)
    try:
        while True:
            async with asyncio.timeout(30):  # Check connection every 30 seconds
                # Optionally send a keep-alive message (not required by client)
                await websocket.send_text("keep-alive")
                await logger.info(f"Sent keep-alive to user {user_id}")

                # Attempt to receive any client message to check connection
                try:
                    data = await websocket.receive_text()
                    await logger.info(f"Received from {user_id}: {data}")
                except WebSocketDisconnect:
                    await logger.info(f"User {user_id} disconnected during receive")
                    await connection_manager.disconnect(websocket, user_id)
                    break
    except asyncio.TimeoutError:
        await logger.warning(f"Timeout waiting for activity from user {user_id}")
        await connection_manager.disconnect(websocket, user_id)
    except WebSocketDisconnect:
        await logger.info(f"User {user_id} disconnected")
        await connection_manager.disconnect(websocket, user_id)
    except Exception as e:
        await logger.error(f"Unexpected error for user {user_id}: {str(e)}")
        await connection_manager.disconnect(websocket, user_id)