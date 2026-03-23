# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import IO
from typing import TYPE_CHECKING
from typing import Any

import httpx

from tika_client._http_backends._protocols import HttpStatusError

if TYPE_CHECKING:
    from tika_client._http_backends._protocols import ResponseProtocol


class HttpxResponseAdapter:
    """Wraps an httpx.Response to satisfy ResponseProtocol."""

    def __init__(self, response: httpx.Response) -> None:
        """Initialize with an httpx response."""
        self._response = response

    @property
    def status_code(self) -> int:
        """HTTP status code."""
        return self._response.status_code

    def raise_for_status(self) -> None:
        """Raise HttpStatusError for 4xx/5xx responses."""
        try:
            self._response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HttpStatusError(response=self) from e

    def json(self) -> Any:  # noqa: ANN401
        """Parse response body as JSON."""
        return self._response.json()


class HttpxSyncAdapter:
    """Synchronous HTTP adapter backed by httpx.Client."""

    def __init__(self, client: httpx.Client) -> None:
        """Initialize with an httpx sync client."""
        self._client = client

    def post(
        self,
        url: str,
        *,
        files: dict[str, tuple[str, IO[bytes], str]],
        headers: dict[str, str],
    ) -> ResponseProtocol:
        """Perform a POST request with multipart file upload."""
        return HttpxResponseAdapter(self._client.post(url, files=files, headers=headers))

    def put(
        self,
        url: str,
        *,
        content: bytes,
        headers: dict[str, str],
    ) -> ResponseProtocol:
        """Perform a PUT request with raw byte content."""
        return HttpxResponseAdapter(self._client.put(url, content=content, headers=headers))

    def close(self) -> None:
        """Close the underlying httpx client."""
        self._client.close()


class HttpxAsyncAdapter:
    """Asynchronous HTTP adapter backed by httpx.AsyncClient."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        """Initialize with an httpx async client."""
        self._client = client

    async def post(
        self,
        url: str,
        *,
        files: dict[str, tuple[str, IO[bytes], str]],
        headers: dict[str, str],
    ) -> ResponseProtocol:
        """Perform an async POST request with multipart file upload."""
        return HttpxResponseAdapter(await self._client.post(url, files=files, headers=headers))

    async def put(
        self,
        url: str,
        *,
        content: bytes,
        headers: dict[str, str],
    ) -> ResponseProtocol:
        """Perform an async PUT request with raw byte content."""
        return HttpxResponseAdapter(await self._client.put(url, content=content, headers=headers))

    async def aclose(self) -> None:
        """Close the underlying httpx async client."""
        await self._client.aclose()
