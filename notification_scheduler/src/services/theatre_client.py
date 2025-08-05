# services/theatre_client.py
import logging
from typing import List, Dict, Any, Optional
import aiohttp
from pydantic import UUID4

from core.config import settings
from core.exceptions import ExternalAPIError
from utils.retry import with_retry

logger = logging.getLogger(__name__)

class TheatreClient:
    """
    Client for interacting with the Theatre API.
    Handles fetching film information.
    """

    def __init__(self):
        self.base_url = settings.ugc_crud_host
        self.secret_key = settings.NOTIFICATION_API_SECRET_KEY

    async def _get_headers(self) -> Dict[str, str]:
        if not self.secret_key:
            raise ExternalAPIError('invalid api key')
        return {'X-Internal-Auth': self.secret_key}

    @with_retry(max_attempts=settings.MAX_RETRIES, delay=settings.RETRY_DELAY)
    async def get_recommended_films(self, user_id: Optional[UUID4] = None) -> List[Dict[str, Any]]:
        """Get recommended films for a user or general recommendations"""
        if user_id:
            logger.info(f"Fetching recommended films for user {user_id}")
            url = f"{self.base_url}/api/v1/films/recommendations/{user_id}"
        else:
            logger.info("Fetching general film recommendations")
            url = f"{self.base_url}/api/v1/films/recommendations"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=await self._get_headers()) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to get films from Theatre API: {error_text}")
                        raise ExternalAPIError(
                            message=f"Theatre API returned {response.status}",
                            service_name="theatre",
                            status_code=response.status,
                            details={"error": error_text}
                        )

                    data = await response.json()
                    logger.debug(f"Retrieved {len(data)} recommended films")
                    return data
            except aiohttp.ClientError as e:
                logger.error(f"Error connecting to Theatre API: {str(e)}")
                raise ExternalAPIError(
                    message=f"Failed to connect to Theatre API: {str(e)}",
                    service_name="theatre",
                    details={"error": str(e)}
                )
