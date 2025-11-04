"""
Temponest SDK Base Client
"""
import os
import httpx
from typing import Optional, Dict, Any, Union
from urllib.parse import urljoin

from .exceptions import (
    TemponestAPIError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
    ConnectionError as TemponestConnectionError,
    TimeoutError as TemponestTimeoutError,
    ConfigurationError,
)


class BaseClient:
    """Base HTTP client for Temponest API"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff_factor: float = 0.5,
        verify_ssl: bool = True,
    ):
        """
        Initialize the base client

        Args:
            base_url: Base URL for the API (default: from TEMPONEST_BASE_URL env var)
            auth_token: Authentication token (default: from TEMPONEST_AUTH_TOKEN env var)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_backoff_factor: Backoff factor for retries
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url or os.getenv("TEMPONEST_BASE_URL", "http://localhost:9000")
        self.auth_token = auth_token or os.getenv("TEMPONEST_AUTH_TOKEN")

        if not self.base_url:
            raise ConfigurationError("base_url must be provided or TEMPONEST_BASE_URL must be set")

        # Ensure base_url ends with /
        if not self.base_url.endswith("/"):
            self.base_url += "/"

        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor

        # Create HTTP client
        self.client = httpx.Client(
            timeout=timeout,
            verify=verify_ssl,
            follow_redirects=True,
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "temponest-sdk/1.0.0",
        }

        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        return headers

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle HTTP error responses"""
        try:
            error_data = response.json()
            message = error_data.get("detail", response.text)
        except Exception:
            message = response.text

        status_code = response.status_code

        if status_code == 401:
            raise AuthenticationError(message, status_code=status_code)
        elif status_code == 403:
            raise AuthorizationError(message, status_code=status_code)
        elif status_code == 404:
            raise NotFoundError(message, status_code=status_code)
        elif status_code == 422:
            raise ValidationError(message, status_code=status_code)
        elif status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message,
                status_code=status_code,
                retry_after=int(retry_after) if retry_after else None
            )
        elif status_code >= 500:
            raise ServerError(message, status_code=status_code)
        else:
            raise TemponestAPIError(message, status_code=status_code)

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Make an HTTP request

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: API endpoint path
            params: Query parameters
            json: JSON body
            data: Form data
            files: Files to upload

        Returns:
            Response data

        Raises:
            TemponestAPIError: On API errors
        """
        url = urljoin(self.base_url, path.lstrip("/"))
        headers = self._get_headers()

        # Remove Content-Type for file uploads
        if files:
            headers.pop("Content-Type", None)

        try:
            response = self.client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                data=data,
                files=files,
                headers=headers,
            )

            # Check for errors
            if response.status_code >= 400:
                self._handle_error(response)

            # Return JSON response if available
            if response.content:
                try:
                    return response.json()
                except Exception:
                    return response.text

            return None

        except httpx.TimeoutException as e:
            raise TemponestTimeoutError(f"Request timed out after {self.timeout}s: {str(e)}")
        except httpx.NetworkError as e:
            raise TemponestConnectionError(f"Network error: {str(e)}")
        except httpx.HTTPError as e:
            raise TemponestAPIError(f"HTTP error: {str(e)}")

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make a GET request"""
        return self._request("GET", path, params=params)

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make a POST request"""
        return self._request("POST", path, json=json, data=data, files=files)

    def put(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        """Make a PUT request"""
        return self._request("PUT", path, json=json)

    def patch(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        """Make a PATCH request"""
        return self._request("PATCH", path, json=json)

    def delete(self, path: str) -> Any:
        """Make a DELETE request"""
        return self._request("DELETE", path)

    def close(self) -> None:
        """Close the HTTP client"""
        self.client.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class AsyncBaseClient:
    """Async base HTTP client for Temponest API"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff_factor: float = 0.5,
        verify_ssl: bool = True,
    ):
        """Initialize the async base client"""
        self.base_url = base_url or os.getenv("TEMPONEST_BASE_URL", "http://localhost:9000")
        self.auth_token = auth_token or os.getenv("TEMPONEST_AUTH_TOKEN")

        if not self.base_url:
            raise ConfigurationError("base_url must be provided or TEMPONEST_BASE_URL must be set")

        if not self.base_url.endswith("/"):
            self.base_url += "/"

        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor

        self.client = httpx.AsyncClient(
            timeout=timeout,
            verify=verify_ssl,
            follow_redirects=True,
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "temponest-sdk/1.0.0",
        }

        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        return headers

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle HTTP error responses"""
        try:
            error_data = response.json()
            message = error_data.get("detail", response.text)
        except Exception:
            message = response.text

        status_code = response.status_code

        if status_code == 401:
            raise AuthenticationError(message, status_code=status_code)
        elif status_code == 403:
            raise AuthorizationError(message, status_code=status_code)
        elif status_code == 404:
            raise NotFoundError(message, status_code=status_code)
        elif status_code == 422:
            raise ValidationError(message, status_code=status_code)
        elif status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message,
                status_code=status_code,
                retry_after=int(retry_after) if retry_after else None
            )
        elif status_code >= 500:
            raise ServerError(message, status_code=status_code)
        else:
            raise TemponestAPIError(message, status_code=status_code)

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make an async HTTP request"""
        url = urljoin(self.base_url, path.lstrip("/"))
        headers = self._get_headers()

        if files:
            headers.pop("Content-Type", None)

        try:
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                data=data,
                files=files,
                headers=headers,
            )

            if response.status_code >= 400:
                self._handle_error(response)

            if response.content:
                try:
                    return response.json()
                except Exception:
                    return response.text

            return None

        except httpx.TimeoutException as e:
            raise TemponestTimeoutError(f"Request timed out after {self.timeout}s: {str(e)}")
        except httpx.NetworkError as e:
            raise TemponestConnectionError(f"Network error: {str(e)}")
        except httpx.HTTPError as e:
            raise TemponestAPIError(f"HTTP error: {str(e)}")

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make an async GET request"""
        return await self._request("GET", path, params=params)

    async def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make an async POST request"""
        return await self._request("POST", path, json=json, data=data, files=files)

    async def put(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        """Make an async PUT request"""
        return await self._request("PUT", path, json=json)

    async def patch(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        """Make an async PATCH request"""
        return await self._request("PATCH", path, json=json)

    async def delete(self, path: str) -> Any:
        """Make an async DELETE request"""
        return await self._request("DELETE", path)

    async def close(self) -> None:
        """Close the async HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
