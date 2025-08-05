from functools import lru_cache
import json
import logging
from http import HTTPStatus

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from models.entity import Notification, ContentDB, NotificationDB
from db.postgres import get_session
from db.broker import get_broker, RabbitMQBroker
from db.db_engine import get_db_engine, DBEngine
from core.config import settings


class NotificationService:
    def __init__(
        self,
        db_session: AsyncSession,
        broker: RabbitMQBroker,
        db_engine: DBEngine,
    ):
        self.db_session = db_session
        self.broker = broker
        self.db_engine = db_engine

    async def send_notification(self, notification_data: Notification) -> None:
        """Запись уведомления в базу данных
        и отправка информации о нем в брокер"""
        logging.info(f"Sending notification: {notification_data}")

        template = await self.db_engine.get_template_by_type(
            notification_data.content_key.split("/")[0]
        )
        if not template:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Template not found",
            )
        template_id = template.id

        content_id = ""
        if notification_data.content_key and notification_data.content_data:
            content = ContentDB(
                key=notification_data.content_key,
                value=notification_data.content_data,
            )
            try:
                content_id = await self.db_engine.add_content(content)
            except Exception as e:
                logging.error(f"Error adding content to database: {e}")
                raise e

        notification = NotificationDB(
            template_id=template_id,
            content_id=str(content_id),
        )
        try:
            notification_id = await self.db_engine.add_notification(
                notification
            )
        except Exception as e:
            logging.error(f"Error adding notification to database: {e}")
            raise e

        json_message = json.dumps(
            {
                "notification_id": str(notification_id),
                "to_id": notification_data.to_id,
                "send_by": notification_data.send_by,
            }
        )
        try:
            await self.broker.send_message(
                queue=settings.queue_for_worker, message=json_message
            )
        except Exception as e:
            logging.error(f"Error sending message to broker: {e}")
            raise e

    async def get_template(self, notification_id: str) -> str:
        """Получение шаблона уведомления по его ID"""
        template = await self.db_engine.get_template_by_notification_id(
            notification_id
        )
        if not template:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Template not found",
            )
        return template.template

    async def set_notification_sent(self, notification_id: str) -> None:
        """Установка уведомления как отправленного"""
        # sent = await self.db_engine.set_notification_sent(notification_id)
        sent = await self.db_engine.delete_notification(notification_id)
        if not sent:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Notification not sent",
            )


@lru_cache()
def get_notification_service(
    session: AsyncSession = Depends(get_session),
    broker: RabbitMQBroker = Depends(get_broker),
    db_engine: DBEngine = Depends(get_db_engine),
) -> NotificationService:
    return NotificationService(
        db_session=session, broker=broker, db_engine=db_engine
    )
