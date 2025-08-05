from typing import Any
import logging

import aiohttp

from exception.app import AppException


class ApiService:
    def __init__(self, secret_key) -> None:
        connector = aiohttp.TCPConnector(ssl=False, force_close=True)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        self.secret_key = secret_key

    def _get_auth_headers(self):
        if not self.secret_key:
            raise AppException('invalid api key')
        return {'X-Internal-Auth': self.secret_key}

    async def post_data(self, url: str, params: dict, json_body: dict) -> dict[str, Any]:
        headers = self._get_auth_headers()
        logging.info(f'Making POST request to: {url}')
        async with self.session.post(url, params=params, json=json_body, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    async def get_data(self, url: str) -> dict[str, Any]:
        headers = self._get_auth_headers()
        logging.info(f'Making GET request to: {url}')
        async with self.session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    async def close(self):
        await self.session.close()
