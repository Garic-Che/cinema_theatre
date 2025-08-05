# services/ugc_client.py
import logging
from typing import List, Dict, Any
import aiohttp
from pydantic import UUID4

from core.config import settings
from core.exceptions import ExternalAPIError
from utils.retry import with_retry

logger = logging.getLogger(__name__)

class UGCClient:
    """
    Client for interacting with the UGC CRUD API.
    Handles fetching user-generated content like bookmarks, likes, and comments.
    """
    def __init__(self):
        self.base_url = settings.ugc_crud_host
        self.secret_key = settings.UGC_CRUD_API_SECRET_KEY

    async def _get_headers(self) -> Dict[str, str]:
        if not self.secret_key:
            raise ExternalAPIError('invalid api key')
        return {'X-Internal-Auth': self.secret_key}

    @with_retry(max_attempts=settings.MAX_RETRIES, delay=settings.RETRY_DELAY)
    async def get_user_bookmarks(self, user_id: UUID4) -> List[Dict[str, Any]]:
        """Get all bookmarks for a user"""
        logger.info(f"Fetching bookmarks for user {user_id}")

        url = f"{self.base_url}/api/v1/bookmarks/user/{user_id}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=await self._get_headers()) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to get bookmarks from UGC API: {error_text}")
                        raise ExternalAPIError(
                            message=f"UGC API returned {response.status}",
                            service_name="ugc",
                            status_code=response.status,
                            details={"error": error_text}
                        )

                    data = await response.json()
                    logger.debug(f"Retrieved {len(data)} bookmarks for user {user_id}")
                    return data
            except aiohttp.ClientError as e:
                logger.error(f"Error connecting to UGC API: {str(e)}")
                raise ExternalAPIError(
                    message=f"Failed to connect to UGC API: {str(e)}",
                    service_name="ugc",
                    details={"error": str(e)}
                )

    @with_retry(max_attempts=settings.MAX_RETRIES, delay=settings.RETRY_DELAY)
    async def get_user_likes(self, user_id: UUID4) -> List[Dict[str, Any]]:
        """Get all likes for a user"""
        logger.info(f"Fetching likes for user {user_id}")

        url = f"{self.base_url}/api/v1/likes/user/{user_id}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=await self._get_headers()) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to get likes from UGC API: {error_text}")
                        raise ExternalAPIError(
                            message=f"UGC API returned {response.status}",
                            service_name="ugc",
                            status_code=response.status,
                            details={"error": error_text}
                        )

                    data = await response.json()
                    logger.debug(f"Retrieved {len(data)} likes for user {user_id}")
                    return data
            except aiohttp.ClientError as e:
                logger.error(f"Error connecting to UGC API: {str(e)}")
                raise ExternalAPIError(
                    message=f"Failed to connect to UGC API: {str(e)}",
                    service_name="ugc",
                    details={"error": str(e)}
                )
