"""User data handler for BD Data Fetcher."""

from typing import Any, Dict, List

import structlog
from pydantic import BaseModel

from .base import BaseDataHandler

logger = structlog.get_logger(__name__)


class UserData(BaseModel):
    """User data model."""
    
    id: int
    name: str
    email: str
    username: str
    phone: str = ""
    website: str = ""
    company: Dict[str, str] = {}


class UserDataHandler(BaseDataHandler):
    """Handler for user data operations."""
    
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        """Fetch user data from the API.
        
        Args:
            **kwargs: Additional parameters (e.g., limit, offset)
            
        Returns:
            Raw user data from API
        """
        endpoint = "/users"
        params = {
            "limit": kwargs.get("limit", 100),
            "offset": kwargs.get("offset", 0),
        }
        
        logger.info("Fetching user data", endpoint=endpoint, params=params)
        return self.api_client.get(endpoint, params=params)
    
    def process_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process raw user data into structured format.
        
        Args:
            data: Raw user data from API
            
        Returns:
            List of processed user records
        """
        users = data.get("users", []) if isinstance(data, dict) else data
        
        processed_users = []
        for user in users:
            try:
                # Validate and clean user data
                user_data = UserData(
                    id=user.get("id"),
                    name=user.get("name", ""),
                    email=user.get("email", ""),
                    username=user.get("username", ""),
                    phone=user.get("phone", ""),
                    website=user.get("website", ""),
                    company=user.get("company", {}),
                )
                
                processed_users.append(user_data.model_dump())
                
            except Exception as e:
                logger.warning("Failed to process user record", user_id=user.get("id"), error=str(e))
                continue
        
        logger.info("User data processed", total_users=len(users), processed_users=len(processed_users))
        return processed_users
    
    def fetch_user_by_id(self, user_id: int) -> Dict[str, Any]:
        """Fetch a specific user by ID.
        
        Args:
            user_id: User ID to fetch
            
        Returns:
            User data
        """
        endpoint = f"/users/{user_id}"
        logger.info("Fetching user by ID", user_id=user_id)
        return self.api_client.get(endpoint)
    
    def search_users(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search users by query.
        
        Args:
            query: Search query
            **kwargs: Additional search parameters
            
        Returns:
            List of matching users
        """
        endpoint = "/users/search"
        params = {"q": query, **kwargs}
        
        logger.info("Searching users", query=query, params=params)
        raw_data = self.api_client.get(endpoint, params=params)
        return self.process_data(raw_data) 