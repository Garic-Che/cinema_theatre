# src/services/auth_client.py
"""
HTTP client for AuthAPI integration.
"""

import logging
from typing import List, Optional

import httpx

from core.config import settings
from schemas.notification import UserModel
from utils.retry import with_retry


class AuthAPIClient:
    """Client for interacting with the Auth API service."""
    
    def __init__(self):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.base_url = self.settings.auth_host
        
        self.client_config = {
            "timeout": httpx.Timeout(30),
            "limits": httpx.Limits(max_keepalive_connections=10, max_connections=20),
        }
    
    @with_retry()
    async def get_users_by_group(self, group_name: str) -> List[UserModel]:
        """
        Fetch users belonging to a specific group/role.
        
        Args:
            group_name: The name of the group to fetch users for
            
        Returns:
            List of UserModel instances
        """
        try:
            async with httpx.AsyncClient(**self.client_config) as client:
                # Assuming the API endpoint structure
                response = await client.get(
                    f"{self.base_url}/api/v1/users/group/{group_name}",
                    headers={
                        "X-Internal-Auth": self.settings.INTERNAL_AUTH_SECRET_KEY
                    },
                )
                
                if response.status_code == 200:
                    users_data = response.json()
                    users = [UserModel(**user_data) for user_data in users_data.get("users", [])]
                    self.logger.info(f"Retrieved {len(users)} users for group '{group_name}'")
                    return users
                else:
                    self.logger.error(
                        f"Failed to fetch users for group '{group_name}': "
                        f"HTTP {response.status_code} - {response.text}"
                    )
                    return []
                    
        except httpx.RequestError as e:
            self.logger.error(f"Request error when fetching users: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error when fetching users: {str(e)}")
            return []
    
    @with_retry()
    async def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        """
        Fetch a specific user by ID.
        
        Args:
            user_id: The user ID to fetch
            
        Returns:
            UserModel instance or None if not found
        """
        try:
            async with httpx.AsyncClient(**self.client_config) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/{user_id}",
                    headers={
                        "X-Internal-Auth": self.settings.INTERNAL_AUTH_SECRET_KEY
                    },
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    user = UserModel(**user_data)
                    self.logger.debug(f"Retrieved user {user_id}")
                    return user
                elif response.status_code == 404:
                    self.logger.warning(f"User {user_id} not found")
                    return None
                else:
                    self.logger.error(
                        f"Failed to fetch user {user_id}: "
                        f"HTTP {response.status_code} - {response.text}"
                    )
                    return None
                    
        except httpx.RequestError as e:
            self.logger.error(f"Request error when fetching user {user_id}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error when fetching user {user_id}: {str(e)}")
            return None
    
    @with_retry()
    async def get_users_with_roles(self, roles: List[str]) -> List[UserModel]:
        """
        Fetch users with specific roles.
        
        Args:
            roles: List of role names to filter by
            
        Returns:
            List of UserModel instances
        """
        try:
            async with httpx.AsyncClient(**self.client_config) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/roles/{",".join(roles)}",
                    headers={
                        "X-Internal-Auth": self.settings.INTERNAL_AUTH_SECRET_KEY
                    },
                )
                
                if response.status_code == 200:
                    users_data = response.json()
                    users = [UserModel(**user_data) for user_data in users_data.get("users", [])]
                    self.logger.info(f"Retrieved {len(users)} users with roles {roles}")
                    return users
                else:
                    self.logger.error(
                        f"Failed to fetch users with roles {roles}: "
                        f"HTTP {response.status_code} - {response.text}"
                    )
                    return []
                    
        except httpx.RequestError as e:
            self.logger.error(f"Request error when fetching users with roles: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error when fetching users with roles: {str(e)}")
            return []