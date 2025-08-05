from jose import jwt
import time
import dotenv
from core.config import settings

dotenv.load_dotenv(".env")

secret_key = "INTERNAL_AUTH_SECRET_KEY"  # Замените на ваш settings.jwt_secret_key
algorithm = "HS256"
user_id = "02a15566-6bcf-4a0d-9570-d04317da1e6b"
payload = {
    "user_id": user_id,
    "roles": [],
    "jti": "e7862a08-79e9-4f43-abb1-6840b8c4657d",
    "exp": int(time.time()) + 36000  # Срок действия 1 час
}
token = jwt.encode(payload, secret_key, algorithm=algorithm)
print(token)

from service.bearer import decode_token
result = decode_token(token)
print(result)

import asyncio
import json
import websockets
from aio_pika import connect_robust, Message

# Конфигурация
WS_URI = "ws://localhost:80/ws"
RABBITMQ_URI = "amqp://guest:123123@localhost:5672/"
QUEUE_NAME =  "notification_websocket"
TEST_USER_ID = user_id
TEST_TOKEN = token  # В реальном тесте используйте валидный JWT


async def websocket_client():
    """Подключается к WebSocket и слушает сообщения."""
    try:
        headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
        async with websockets.connect(WS_URI, additional_headers=headers) as ws:
            print("✅ WebSocket подключен")

            # Первое сообщение - keep-alive
            greeting = await ws.recv()
            print(f"🔄 Получено: {greeting}")

            # Ждем уведомление (таймаут 15 сек)
            try:
                notification = await asyncio.wait_for(ws.recv(), timeout=15)
                print(f"🎉 Получено уведомление: {notification}")
            except asyncio.TimeoutError:
                print("❌ Уведомление не пришло (таймаут)")

    except Exception as e:
        print(f"❌ Ошибка WebSocket: {str(e)}")
        raise


async def send_rabbitmq_message():
    """Отправляет тестовое сообщение в RabbitMQ."""
    try:
        # Подключение с таймаутом и повторными попытками
        for attempt in range(3):
            try:
                connection = await asyncio.wait_for(
                    connect_robust(RABBITMQ_URI),
                    timeout=5
                )
                break
            except Exception as e:
                if attempt == 2:
                    raise
                print(f"⚠ Попытка {attempt + 1}/3: Ошибка подключения к RabbitMQ: {str(e)}")
                await asyncio.sleep(2)

        async with connection:
            channel = await connection.channel()
            await channel.declare_queue(QUEUE_NAME, durable=True)

            message = {
                "notification_id": "test_notification_123",
                "to_id": TEST_USER_ID
            }

            await channel.default_exchange.publish(
                Message(body=json.dumps(message).encode()),
                routing_key=QUEUE_NAME
            )
            print("📨 Сообщение отправлено в RabbitMQ")

    except Exception as e:
        print(f"❌ Ошибка RabbitMQ: {str(e)}")
        raise


async def main():
    print(f"🔍 Тестирование для user_id: {TEST_USER_ID}")

    # Запускаем клиент WebSocket
    ws_task = asyncio.create_task(websocket_client())

    # Даем время на подключение
    await asyncio.sleep(2)

    # Отправляем тестовое уведомление
    await send_rabbitmq_message()

    # Ждем завершения клиента
    await ws_task


if __name__ == "__main__":
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())