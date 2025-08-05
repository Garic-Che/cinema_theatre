# src/services/notification_client.py
"""
HTTP client for NotificationAPI integration.
"""

import logging
from typing import Dict, Any

import httpx

from core.config import settings
from schemas.notification import NotificationRequest, NotificationContent
from utils.retry import with_retry


class NotificationAPIClient:
    """Client for sending notifications via the Notification API service."""
    
    def __init__(self):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.base_url = self.settings.NOTIFICATION_SERVICE_HOST
        
        self.client_config = {
            "timeout": httpx.Timeout(self.settings.API_TIMEOUT),
            "limits": httpx.Limits(max_keepalive_connections=10, max_connections=20),
        }
    
    @with_retry()
    async def send_notification(
            self,
            user_id: str,
            content_key: str,
            content_data: NotificationContent,
            send_by: str = "email"
    ) -> bool:
        """
        Send a notification to a specific user.
        """
        try:
            notification_request = NotificationRequest(
                to_id=user_id,
                send_by=send_by,
                content_key=content_key,
                content_data=content_data
            )

            # Логирование для отладки
            self.logger.debug(f"Sending notification to {user_id} with content key {content_key}")

            async with httpx.AsyncClient(**self.client_config) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/notification",
                    json=notification_request.dict(),
                    headers={
                        "Content-Type": "application/json",
                        "X-Internal-Auth": self.settings.NOTIFICATION_API_SECRET_KEY,
                    },
                )

                if response.status_code in (200, 201, 202):
                    self.logger.debug(f"Notification sent successfully to {user_id}")
                    return True
                else:
                    self.logger.error(
                        f"Failed to send notification to {user_id}: "
                        f"HTTP {response.status_code} - {response.text}"
                    )
                    return False

        except Exception as e:
            self.logger.error(f"Error sending notification to {user_id}: {str(e)}")
            return False
    
    @with_retry()
    async def send_bulk_notifications(
        self,
        notifications: list[NotificationRequest]
    ) -> Dict[str, bool]:
        """
        Send multiple notifications in bulk.
        
        Args:
            notifications: List of notification requests
            
        Returns:
            Dictionary mapping user_id to success status
        """
        results = {}
        
        try:
            async with httpx.AsyncClient(**self.client_config) as client:
                # Send notifications in batches to avoid overwhelming the service
                batch_size = 10
                for i in range(0, len(notifications), batch_size):
                    batch = notifications[i:i + batch_size]
                    
                    # Process batch concurrently
                    tasks = []
                    for notification in batch:
                        task = self._send_single_notification(client, notification)
                        tasks.append(task)
                    
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    for notification, result in zip(batch, batch_results):
                        if isinstance(result, Exception):
                            self.logger.error(
                                f"Error sending notification to {notification.to_id}: {str(result)}"
                            )
                            results[notification.to_id] = False
                        else:
                            results[notification.to_id] = result
            
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            self.logger.info(f"Bulk notification results: {successful}/{total} successful")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in bulk notification sending: {str(e)}")
            # Return failed status for all notifications
            return {notif.to_id: False for notif in notifications}
    
    async def _send_single_notification(
        self,
        client: httpx.AsyncClient,
        notification: NotificationRequest
    ) -> bool:
        """Send a single notification using the provided client."""
        try:
            response = await client.post(
                f"{self.base_url}/api/v1/notification",
                json=notification.dict(),
                headers={
                    "Content-Type": "application/json",
                    "X-Internal-Auth": self.settings.NOTIFICATION_API_SECRET_KEY,
                },
            )
            
            return response.status_code in (200, 201, 202)
            
        except Exception as e:
            self.logger.error(
                f"Error sending notification to {notification.to_id}: {str(e)}"
            )
            return False