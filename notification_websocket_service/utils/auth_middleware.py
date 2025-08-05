from functools import wraps
from http import HTTPStatus

from fastapi import WebSocket, WebSocketDisconnect

from core.config import settings

def websocket_internal_auth_required(func):
    @wraps(func)
    async def decorated_function(websocket: WebSocket, *args, **kwargs):
        try:
            # Получаем токен из query параметров или заголовков
            token = websocket.query_params.get("token") or \
                    websocket.headers.get("x-internal-auth")

            if not token:
                await websocket.close(code=HTTPStatus.UNAUTHORIZED)
                return

            if token != settings.notification_api_secret_key:
                await websocket.close(code=HTTPStatus.FORBIDDEN)
                return

            return await func(websocket, *args, **kwargs)
        except WebSocketDisconnect:
            # Обработка разрыва соединения
            raise
        except Exception:
            await websocket.close(code=HTTPStatus.INTERNAL_SERVER_ERROR)
            raise

    return decorated_function