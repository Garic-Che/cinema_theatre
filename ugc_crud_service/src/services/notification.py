import httpx

from core.config import Settings
from schemas.model import Notification


class NotificationService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def send_notification(self, notification: Notification) -> None:
        url = (
            f"{self.settings.notification_service_scheme}://"
            f"{self.settings.notification_service_host}:"
            f"{self.settings.notification_service_port}/api/v1/notification"
        )
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=notification.model_dump(),
                headers={
                    "X-Internal-Auth": self.settings.notification_api_secret_key
                },
            )
            return response.json()


def get_notification_service(settings: Settings) -> NotificationService:
    return NotificationService(settings)
