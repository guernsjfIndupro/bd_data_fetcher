"""Tests for API client."""

import pytest
from unittest.mock import Mock, patch
from requests.exceptions import RequestException

from bd_data_fetcher.api.client import APIClient, APIConfig, APIError


class TestAPIConfig:
    """Test API configuration."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = APIConfig(base_url="https://api.example.com")
        assert config.base_url == "https://api.example.com"
        assert config.api_key is None
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
    
    def test_config_custom_values(self):
        """Test custom configuration values."""
        config = APIConfig(
            base_url="https://api.example.com",
            api_key="test_key",
            timeout=60,
            max_retries=5,
            retry_delay=2.0,
        )
        assert config.base_url == "https://api.example.com"
        assert config.api_key == "test_key"
        assert config.timeout == 60
        assert config.max_retries == 5
        assert config.retry_delay == 2.0


class TestAPIClient:
    """Test API client functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        return APIConfig(
            base_url="https://api.example.com",
            api_key="test_key",
            timeout=30,
            max_retries=2,
            retry_delay=0.1,
        )
    
    @pytest.fixture
    def api_client(self, mock_config):
        """Create an API client with mock configuration."""
        return APIClient(mock_config)
    
    def test_client_initialization(self, mock_config):
        """Test client initialization."""
        client = APIClient(mock_config)
        assert client.config == mock_config
        assert client.session is not None
    
    def test_client_with_auth_header(self, mock_config):
        """Test that authentication header is set when API key is provided."""
        client = APIClient(mock_config)
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == "Bearer test_key"
    
    def test_client_without_auth_header(self):
        """Test that no auth header is set when API key is not provided."""
        config = APIConfig(base_url="https://api.example.com")
        client = APIClient(config)
        assert "Authorization" not in client.session.headers
    
    @patch('bd_data_fetcher.api.client.requests.Session')
    def test_successful_get_request(self, mock_session, api_client):
        """Test successful GET request."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status.return_value = None
        mock_session.return_value.request.return_value = mock_response
        
        result = api_client.get("/test")
        
        assert result == {"data": "test"}
        mock_session.return_value.request.assert_called_once()
    
    @patch('bd_data_fetcher.api.client.requests.Session')
    def test_failed_request_with_retry(self, mock_session, api_client):
        """Test request failure with retry logic."""
        # Mock failed response
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = RequestException("Connection error")
        mock_session.return_value.request.return_value = mock_response
        
        with pytest.raises(APIError) as exc_info:
            api_client.get("/test")
        
        assert "Request failed after 2 retries" in str(exc_info.value)
        # Should have been called 3 times (initial + 2 retries)
        assert mock_session.return_value.request.call_count == 3
    
    @patch('bd_data_fetcher.api.client.requests.Session')
    def test_successful_request_after_retry(self, mock_session, api_client):
        """Test successful request after initial failure."""
        # Mock response that fails first, then succeeds
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = RequestException("Connection error")
        
        mock_response_success = Mock()
        mock_response_success.json.return_value = {"data": "test"}
        mock_response_success.raise_for_status.return_value = None
        
        mock_session.return_value.request.side_effect = [
            mock_response_fail,
            mock_response_success
        ]
        
        result = api_client.get("/test")
        
        assert result == {"data": "test"}
        assert mock_session.return_value.request.call_count == 2
    
    def test_context_manager(self, api_client):
        """Test context manager functionality."""
        with api_client as client:
            assert client is api_client
        
        # Session should be closed
        api_client.session.close.assert_called_once()
    
    def test_close_method(self, api_client):
        """Test close method."""
        api_client.close()
        api_client.session.close.assert_called_once()


class TestAPIError:
    """Test API error handling."""
    
    def test_api_error_creation(self):
        """Test API error creation."""
        error = APIError("Test error", status_code=404, response={"error": "Not found"})
        assert error.message == "Test error"
        assert error.status_code == 404
        assert error.response == {"error": "Not found"}
    
    def test_api_error_string_representation(self):
        """Test API error string representation."""
        error = APIError("Test error")
        assert str(error) == "Test error" 