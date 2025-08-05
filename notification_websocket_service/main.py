import asyncio
import json
from http import HTTPStatus
from aiohttp import ClientResponseError, ClientConnectorError
from fastapi import FastAPI
from pydantic import ValidationError
import uvicorn

from schema.notification import NotificationData
from service.api import ApiService
from api.v1.websocket_router import router as websocket_router
from service.broker import get_message_broker
from service.notification import get_notification_service
from connection_manager import ConnectionManager
from core.config import settings
from exception.app import AppException
from aiologger import Logger
from core.logger import logger

app = FastAPI()
app.include_router(websocket_router)
connection_manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    app.state.api_service = ApiService(settings.notification_secret_key)
    # Start consuming messages from the queue
    asyncio.create_task(consume_messages())
    await logger.info("Started message consumer for queue: notification_websocket")

@app.on_event("shutdown")
async def shutdown_event():
    await app.state.api_service.close()


async def process_message(incoming_message: bytes):
    try:
        notification = get_notification_from_bytes(incoming_message)
        await logger.info(f"Processing notification: {notification.dict()}")

        template = await get_template(notification.notification_id)
        await logger.info(f"Retrieved template for notification {notification.notification_id}: {template}")

        success = await connection_manager.send_personal_message(
            template,
            notification.to_id
        )
        await logger.info(f"Send result for user {notification.to_id}: {success}")

        if success:
            await mark_notification_processed(notification.notification_id)
            await logger.info(f"Notification {notification.notification_id} processed and marked as sent")
        else:
            await logger.warning(f"User {notification.to_id} not connected. Saving for retry.")
            retry_file = f"retry_{notification.notification_id}.json"
            try:
                with open(retry_file, "w") as f:
                    json.dump({"notification_id": notification.notification_id, "to_id": notification.to_id}, f)
            except OSError as e:
                await logger.error(f"Failed to save retry file {retry_file}: {str(e)}")
    except AppException as e:
        await logger.error(f"AppException in process_message: {str(e)}")
    except Exception as e:
        await logger.error(f"Unexpected error in process_message: {str(e)}")
        raise

async def consume_messages():
    async with get_message_broker() as message_broker:
        queue_name = settings.queue_for_websocket
        await logger.info(f"Starting message consumption from queue: {queue_name}")
        async for incoming_message in message_broker.get_message(queue_name):
            await logger.info(f"Received raw message: {incoming_message.decode('utf-8')}")
            asyncio.create_task(process_message(incoming_message))

def get_notification_from_bytes(message: bytes):
    try:
        raw_message = json.loads(message.decode('utf-8'))
        notification_data = NotificationData(**raw_message)
    except (ValidationError, json.JSONDecodeError, TypeError) as e:
        raise AppException(f'Invalid message format: {str(e)}')
    return notification_data

async def get_template(notification_id: str):
    async with get_notification_service(app.state.api_service) as notification_service:
        try:
            return await notification_service.get_template(notification_id)
        except ClientResponseError as e:
            if e.status == HTTPStatus.NOT_FOUND:
                raise AppException('Notification template not found')
            raise AppException(f'Notification service error: {e.status}')
        except ClientConnectorError:
            raise AppException('Could not connect to notification service')

async def mark_notification_processed(notification_id: str):
    async with get_notification_service(app.state.api_service) as notification_service:
        try:
            await notification_service.set_processed(notification_id)
        except ClientResponseError as e:
            if e.status == HTTPStatus.INTERNAL_SERVER_ERROR:
                raise AppException('Failed to mark notification as processed')
        except ClientConnectorError:
            raise AppException('Could not connect to notification service')

if __name__ == "__main__":
    try:
        uvicorn.run(
            app,
            host=settings.websocket_host,
            port=settings.websocket_port
        )
    except KeyboardInterrupt:
        logging.info("Service stopped by user")
    except Exception as e:
        logging.exception(f"Critical error: {str(e)}")