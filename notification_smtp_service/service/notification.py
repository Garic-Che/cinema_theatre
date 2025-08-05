from abc import ABC, abstractmethod
from contextlib import asynccontextmanager

from .api import ApiService
from core.config import settings


class NotificationServiceABC(ABC):
    @abstractmethod
    async def set_processed(self, notification_id: str) -> None:
        pass

    @abstractmethod
    async def get_template(self, notification_id: str) -> str:
        pass


class NotificationService(NotificationServiceABC):
    def __init__(self, api_service: ApiService) -> None:
        self.api_service = api_service
        host = settings.notification_service_host
        port = settings.auth_service_port
        self.base_url = f'http://{host}:{port}/api/v1/notification'

    async def set_processed(self, notification_id: str) -> None:
        await self.api_service.post_data(
            url=f'{self.base_url}/sent', 
            params={},
            json_body={'notification_id': notification_id})

    async def get_template(self, notification_id: str):
        template = await self.api_service.get_data(
            url=f'{self.base_url}/template/{notification_id}')
        if not template:
            return None
        return template['template']
    

@asynccontextmanager
async def get_notification_service():
    api_key = settings.notification_secret_key
    notification_api_service = ApiService(api_key)
    try:
        yield NotificationService(notification_api_service)
    finally:
        await notification_api_service.close()
