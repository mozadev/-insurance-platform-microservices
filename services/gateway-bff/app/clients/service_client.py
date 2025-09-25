"""HTTP client for calling microservices."""

import asyncio
from typing import Any
from urllib.parse import urljoin

import httpx
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from ...shared.logging import LoggerMixin


class ServiceClient(LoggerMixin):
    """HTTP client for microservice communication."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.instrumentor = HTTPXClientInstrumentor()

        # Create HTTP client with instrumentation
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )

    async def get(
        self, path: str, headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Make GET request."""
        url = urljoin(self.base_url, path.lstrip("/"))

        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            self.logger.error("HTTP error", status_code=e.response.status_code, url=url)
            raise
        except Exception as e:
            self.logger.error("Request failed", error=str(e), url=url)
            raise

    async def post(
        self, path: str, data: dict[str, Any], headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Make POST request."""
        url = urljoin(self.base_url, path.lstrip("/"))

        try:
            response = await self.client.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            self.logger.error("HTTP error", status_code=e.response.status_code, url=url)
            raise
        except Exception as e:
            self.logger.error("Request failed", error=str(e), url=url)
            raise

    async def put(
        self, path: str, data: dict[str, Any], headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Make PUT request."""
        url = urljoin(self.base_url, path.lstrip("/"))

        try:
            response = await self.client.put(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            self.logger.error("HTTP error", status_code=e.response.status_code, url=url)
            raise
        except Exception as e:
            self.logger.error("Request failed", error=str(e), url=url)
            raise

    async def delete(
        self, path: str, headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Make DELETE request."""
        url = urljoin(self.base_url, path.lstrip("/"))

        try:
            response = await self.client.delete(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            self.logger.error("HTTP error", status_code=e.response.status_code, url=url)
            raise
        except Exception as e:
            self.logger.error("Request failed", error=str(e), url=url)
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class CircuitBreaker:
    """Simple circuit breaker implementation."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def can_execute(self) -> bool:
        """Check if request can be executed."""
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            if (
                self.last_failure_time
                and (asyncio.get_event_loop().time() - self.last_failure_time)
                > self.recovery_timeout
            ):
                self.state = "HALF_OPEN"
                return True
            return False

        if self.state == "HALF_OPEN":
            return True

        return False

    def record_success(self):
        """Record successful request."""
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = asyncio.get_event_loop().time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class ResilientServiceClient(ServiceClient):
    """Service client with circuit breaker and retry logic."""

    def __init__(self, base_url: str, timeout: float = 30.0, max_retries: int = 3):
        super().__init__(base_url, timeout)
        self.circuit_breaker = CircuitBreaker()
        self.max_retries = max_retries

    async def _make_request_with_retry(
        self, method: str, path: str, **kwargs
    ) -> dict[str, Any]:
        """Make request with retry logic."""
        if not self.circuit_breaker.can_execute():
            raise Exception("Circuit breaker is OPEN")

        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                if method.upper() == "GET":
                    result = await self.get(path, **kwargs)
                elif method.upper() == "POST":
                    result = await self.post(path, **kwargs)
                elif method.upper() == "PUT":
                    result = await self.put(path, **kwargs)
                elif method.upper() == "DELETE":
                    result = await self.delete(path, **kwargs)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                self.circuit_breaker.record_success()
                return result

            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                else:
                    self.circuit_breaker.record_failure()
                    raise

        raise last_exception
