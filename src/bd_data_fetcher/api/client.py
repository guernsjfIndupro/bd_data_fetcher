"""REST API client for BD Data Fetcher."""

import os
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests
import structlog
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

logger = structlog.get_logger(__name__)


class APIConfig(BaseModel):
    """Configuration for API client."""
    
    base_url: str = Field(..., description="Base URL for the API")
    api_key: Optional[str] = Field(None, description="API key for authentication")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")


class APIError(Exception):
    """Custom exception for API-related errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class APIClient:
    """Production-grade REST API client with retry logic and proper error handling."""
    
    def __init__(self, config: Optional[APIConfig] = None):
        """Initialize the API client.
        
        Args:
            config: API configuration. If None, will load from environment variables.
        """
        if config is None:
            config = self._load_config_from_env()
        
        self.config = config
        self.session = requests.Session()
        
        # Set up session defaults
        self.session.timeout = config.timeout
        
        # Set up authentication if API key is provided
        if config.api_key:
            self.session.headers.update({"Authorization": f"Bearer {config.api_key}"})
        
        # Set default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "BD-Data-Fetcher/0.1.0",
        })
        
        logger.info("API client initialized", base_url=config.base_url)
    
    def _load_config_from_env(self) -> APIConfig:
        """Load configuration from environment variables."""
        return APIConfig(
            base_url=os.getenv("API_BASE_URL", "https://api.example.com"),
            api_key=os.getenv("API_KEY"),
            timeout=int(os.getenv("API_TIMEOUT", "30")),
            max_retries=int(os.getenv("API_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("API_RETRY_DELAY", "1.0")),
        )
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request with retry logic and error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            headers: Additional headers
            
        Returns:
            Response data as dictionary
            
        Raises:
            APIError: If the request fails after all retries
        """
        url = urljoin(self.config.base_url, endpoint)
        
        # Prepare request
        request_kwargs = {
            "method": method,
            "url": url,
            "json": data,
            "params": params,
        }
        
        if headers:
            request_kwargs["headers"] = headers
        
        # Retry logic
        for attempt in range(self.config.max_retries + 1):
            try:
                logger.debug(
                    "Making API request",
                    method=method,
                    url=url,
                    attempt=attempt + 1,
                    max_retries=self.config.max_retries,
                )
                
                response = self.session.request(**request_kwargs)
                response.raise_for_status()
                
                logger.info(
                    "API request successful",
                    method=method,
                    url=url,
                    status_code=response.status_code,
                )
                
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.warning(
                    "API request failed",
                    method=method,
                    url=url,
                    attempt=attempt + 1,
                    error=str(e),
                )
                
                if attempt == self.config.max_retries:
                    raise APIError(
                        f"Request failed after {self.config.max_retries} retries: {str(e)}",
                        status_code=getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
                        response=getattr(e.response, 'json', lambda: None)() if hasattr(e, 'response') else None,
                    )
                
                # Wait before retrying
                import time
                time.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            Response data
        """
        return self._make_request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a POST request.
        
        Args:
            endpoint: API endpoint path
            data: Request body data
            
        Returns:
            Response data
        """
        return self._make_request("POST", endpoint, data=data)
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a PUT request.
        
        Args:
            endpoint: API endpoint path
            data: Request body data
            
        Returns:
            Response data
        """
        return self._make_request("PUT", endpoint, data=data)
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Response data
        """
        return self._make_request("DELETE", endpoint)
    
    def close(self):
        """Close the session and clean up resources."""
        self.session.close()
        logger.info("API client session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close() 