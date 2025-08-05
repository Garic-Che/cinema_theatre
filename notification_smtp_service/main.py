import json
import logging
from http import client
from email.message import EmailMessage

import asyncio
from pydantic_core import ValidationError
from aiohttp.client_exceptions import ClientResponseError, ClientConnectorError
from aiosmtplib.errors import SMTPServerDisconnected

from service.broker import get_message_broker
from service.auth import get_auth_service
from service.notification import get_notification_service
from service.smtp import get_email_service, EmailServiceABC
from schema.notification import NotificationData
from exception.app import AppException
from core.config import settings
from utils.message_builder import MessageBuilder


async def main() -> None:
    async with get_message_broker() as message_broker, get_email_service() as email_service:
        async for incoming_message in message_broker.get_message(settings.queue_for_smtp):
            try:
                notification = get_notification_from_bytes(incoming_message)
                logging.info(f'received a message: {notification}')

                recipient_email = await get_email_by_user_id(notification.to_id)
                logging.info(f'resolved recipient email address: {recipient_email}')

                template = await get_template(notification.notification_id)
                logging.info('extracted template')

                builder = MessageBuilder().set_content(template).set_recipients([recipient_email]).set_sender()
                await send_email(email_service, builder.build())
                logging.info('email sent successfully')

                await mark_notification_processed(notification.notification_id)
                logging.info(f'{notification.notification_id} marked as processed')
            except AppException as app_exception:
                logging.error(app_exception)


def get_notification_from_bytes(message: bytes):
    try:
        raw_message = json.loads(message.decode('utf-8'))
        notification_data = NotificationData(**raw_message)
    except (json.JSONDecodeError, ValidationError):
        raise AppException('invalid message format')
    else:
        return notification_data


async def get_email_by_user_id(user_id: str):
    async with get_auth_service() as auth_service:
        try:
            email = await auth_service.get_user_email(user_id)
        except ClientResponseError as exception:
            if exception.status == client.NOT_FOUND:
                raise AppException('user not found')
        except ClientConnectorError as exception:
            raise AppException(f'could not connect to auth_service: {exception}')
        else:
            return email


async def get_template(notification_id: str):
    async with get_notification_service() as notification_service:
        try:
            template = await notification_service.get_template(notification_id)
        except ClientResponseError as exception:
            if exception.status == client.NOT_FOUND:
                raise AppException('notification not found')
        except ClientConnectorError as exception:
            raise AppException(f'could not connect to notification_service: {exception}')
        else:
            return template
        

async def send_email(email_service: EmailServiceABC, message: EmailMessage):
    try:
        if not email_service.connected():
            await email_service.connect()
        await email_service.send(message)
    except SMTPServerDisconnected:
        raise AppException('smtp server disconnected')
    except ConnectionRefusedError:
        raise AppException('could not send email')

  
async def mark_notification_processed(notification_id: str):
    async with get_notification_service() as notification_service:
        try:
            await notification_service.set_processed(notification_id)
        except ClientResponseError as exception:
            if exception.status == client.INTERNAL_SERVER_ERROR:
                raise AppException('could not set notification processed')
        except ClientConnectorError as exception:
            raise AppException(f'could not connect to notification_service: {exception}')


if __name__ == "__main__":
    asyncio.run(main())
