from abc import ABC, abstractmethod
from contextlib import asynccontextmanager

from .api import ApiService
from core.config import settings


class AuthServiceABC(ABC):
    @abstractmethod
    async def get_user_email(self, user_id: str):
        pass


class AuthService(AuthServiceABC):
    def __init__(self, api_service: ApiService) -> None:
        self.api_service = api_service
        host = settings.auth_service_host
        port = settings.auth_service_port
        self.base_url = f'http://{host}:{port}/api/v1'

    async def get_user_email(self, user_id: str):
        url = f'{self.base_url}/user/email/{user_id}'
        response = await self.api_service.get_data(url)
        return response.get('detail')
    

@asynccontextmanager
async def get_auth_service():
    api_key = settings.auth_secret_key
    auth_api_service = ApiService(api_key)
    try:
        yield AuthService(auth_api_service)
    finally:
        await auth_api_service.close()
