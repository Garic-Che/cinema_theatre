import httpx
import logging

from core.config import settings, Settings
from schemas.model import Notification


class NotificationServiceEngine:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def send_notification(self, notification: Notification) -> None:
        """Отправка уведомления"""
        url = f"{self.settings.notification_service_url}/api/v1/notification/"
        logging.debug(
            "Отправка уведомления %s по адресу %s",
            notification.model_dump(),
            url,
        )
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=notification.model_dump(),
                headers={
                    "X-Internal-Auth": self.settings.notification_api_secret_key
                },
            )
            logging.debug("Ответ от NotificationService: %s", response.json())
            return response.json()


notification_service_engine = NotificationServiceEngine(settings)
