from typing import Any

from aiohttp import ClientTimeout,ClientSession

from exception.app import AppException

class ApiService:
    def __init__(self, secret_key: str) -> None:
        self.session = ClientSession(timeout=ClientTimeout(total=10))
        self.secret_key = secret_key

    def _get_auth_headers(self):
        if not self.secret_key:
            raise AppException('Invalid API key')
        return {'X-Internal-Auth': self.secret_key}

    async def post_data(self, url: str, json_body: dict) -> dict[str, Any]:
        headers = self._get_auth_headers()
        async with self.session.post(url, json=json_body, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    async def get_data(self, url: str) -> dict[str, Any]:
        headers = self._get_auth_headers()
        async with self.session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    async def close(self):
        await self.session.close()