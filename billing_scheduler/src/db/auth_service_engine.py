import httpx
import logging

from core.config import settings, Settings
from schemas.model import CommonID, RoleWithID


class AuthServiceEngine:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def get_roles(self) -> str:
        """Получение всех ролей"""
        logging.debug("Получение всех ролей из AuthService")
        url = f"{self.settings.auth_service_url}/api/v1/role/"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "X-Internal-Auth": self.settings.internal_auth_secret_key
                },
            )
            response_json = response.json()
            if isinstance(response_json, list):
                return [RoleWithID(**role) for role in response_json]
            logging.error(response)
            return []

    async def assign_role(self, user_id: str, role_id: str) -> str:
        """Назначение роли пользователю"""
        logging.debug("Назначение роли %s пользователю %s", role_id, user_id)
        user_id = str(user_id)
        role_id = str(role_id)
        url = f"{self.settings.auth_service_url}/api/v1/role/assign/{user_id}"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=CommonID(id=role_id).model_dump(),
                headers={
                    "X-Internal-Auth": self.settings.internal_auth_secret_key
                },
            )
            return response.json()

    async def revoke_role(self, user_id: str, role_id: str) -> str:
        """Лишение роли пользователя"""
        logging.debug("Лишение роли %s пользователя %s", role_id, user_id)
        user_id = str(user_id)
        role_id = str(role_id)
        url = f"{self.settings.auth_service_url}/api/v1/role/revoke/{user_id}"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=CommonID(id=role_id).model_dump(),
                headers={
                    "X-Internal-Auth": self.settings.internal_auth_secret_key
                },
            )
            return response.json()


auth_service_engine = AuthServiceEngine(settings)
