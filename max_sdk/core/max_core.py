from typing import Any, Dict, Optional

import httpx
from loguru import logger

from .helper.custom_exception import MaxApiError
from .helper.model_for_params import ApiConfig


class MaxApi:

    def __init__(
        self,
        access_token: Optional[str] = "",
        base_url: str = "",
        timeout: float = 60.0,
        connect_timeout: float = 10.0,
        auto_requests: bool = True,
    ):
        config = ApiConfig(
            base_url=base_url.rstrip("/"),
            access_token=access_token or "",
            timeout=timeout,
            connect_timeout=connect_timeout,
        )
        self.config = config
        self.auto_requests = auto_requests
        self._client: Optional[httpx.AsyncClient] = None
        self._timeout = httpx.Timeout(config.timeout, connect=config.connect_timeout)
        self._session_headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}" if access_token else "",
        }

    async def _setup_session(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                headers=self._session_headers,
            )

    async def __aenter__(self):
        await self._setup_session()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> dict[str, Any] | None:
        """
        Выполняет HTTP запрос к API.
        """
        url = f"{self.config.base_url}{endpoint}"
        request_params = params or {}

        if "Authorization" in self._session_headers:
            auth_value = self._session_headers["Authorization"]
            logger.debug(f"Authorization value: {auth_value[:30] if auth_value else 'EMPTY'}...")

        request_headers = self._session_headers.copy()

        if "Authorization" not in request_headers and self.config.access_token:
            request_headers["Authorization"] = f"Bearer {self.config.access_token}"
            logger.debug("Added Authorization header from config")

        logger.debug(f"After copy, Authorization present: {'Authorization' in request_headers}")

        if headers:
            request_headers.update(headers)
        if body is not None and method.upper() in ["POST", "PUT", "PATCH"]:
            request_headers["Content-Type"] = "application/json"

        if body:
            logger.debug(f"Body: {body}")

        try:
            if not self.auto_requests or self._client is None:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        params=request_params,
                        json=body,
                        headers=request_headers,
                    )
            else:
                response = await self._client.request(
                    method=method,
                    url=url,
                    params=request_params,
                    json=body,
                    headers=request_headers,
                )

            return self._handle_response(response)

        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except httpx.RequestError as e:
            self._handle_request_error(e)
        except Exception as e:
            self._handle_unexpected_error(e)

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        self._log_response(response)
        response.raise_for_status()

        if response.status_code == 204:
            return {"success": True}

        content_type = response.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            try:
                return response.json()
            except Exception as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise MaxApiError(
                    message=f"Invalid JSON response: {str(e)}",
                    code="INVALID_JSON",
                    status_code=response.status_code,
                ) from e

        return {"text": response.text}

    @staticmethod
    def _handle_http_error(e: httpx.HTTPStatusError) -> None:
        logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")

        try:
            error_data = e.response.json()
            error_msg = error_data.get("message", error_data.get("error", str(e)))
            error_code = error_data.get("code", f"HTTP_{e.response.status_code}")
        except ValueError:
            error_msg = e.response.text or str(e)
            error_code = f"HTTP_{e.response.status_code}"

        raise MaxApiError(message=error_msg, code=error_code, status_code=e.response.status_code) from e

    @staticmethod
    def _handle_request_error(e: httpx.RequestError) -> None:
        logger.error(f"Request error: {e}")
        raise MaxApiError(message=f"Network error: {str(e)}", code="NETWORK_ERROR", status_code=0) from e

    @staticmethod
    def _handle_unexpected_error(e: Exception) -> None:
        logger.error(f"Unexpected error: {e}")
        raise MaxApiError(
            message=f"Unexpected error: {str(e)}",
            code="UNEXPECTED_ERROR",
            status_code=0,
        ) from e

    @staticmethod
    def _log_response(response: httpx.Response) -> None:
        logger.debug(f"Request: {response.request.method} {response.request.url}")
        logger.debug(f"Response status: {response.status_code}")

        if response.text:
            if len(response.text) < 1000:
                logger.debug(f"Response body: {response.text}")
            else:
                logger.debug(f"Response body length: {len(response.text)} chars")
