from contextlib import asynccontextmanager
from tenacity import retry, stop_after_attempt, wait_exponential

from service.api import ApiService
from core.config import settings

class NotificationService:
    def __init__(self, api_service: ApiService) -> None:
        self.api_service = api_service
        host = settings.notification_service_host
        port = settings.notification_service_port  # Add this line
        self.base_url = f'http://{host}:{port}/api/v1/notification'  # Include port

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_template(self, notification_id: str) -> str:
        url = f'{self.base_url}/template/{notification_id}'
        response = await self.api_service.get_data(url)
        return response['template']

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def set_processed(self, notification_id: str) -> None:
        url = f'{self.base_url}/sent'
        payload = {'notification_id': notification_id}
        await self.api_service.post_data(url, payload)

@asynccontextmanager
async def get_notification_service(api_service: ApiService):
    yield NotificationService(api_service)