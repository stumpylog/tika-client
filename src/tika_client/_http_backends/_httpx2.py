# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import IO
from typing import TYPE_CHECKING
from typing import Any

import httpx2

from tika_client._http_backends._streaming import aiter_file
from tika_client._http_backends._streaming import iter_file
from tika_client.exceptions import HttpStatusError

if TYPE_CHECKING:
    from tika_client._http_backends._protocols import ResponseProtocol


class Httpx2ResponseAdapter:
    """Wraps an httpx2.Response to satisfy ResponseProtocol."""

    def __init__(self, response: httpx2.Response) -> None:
        """Initialize with an httpx2 response."""
        self._response = response

    @property
    def status_code(self) -> int:
        """HTTP status code."""
        return self._response.status_code

    @property
    def text(self) -> str:
        """Raw response body as text."""
        return self._response.text

    @property
    def headers(self) -> httpx2.Headers:
        """Response headers."""
        return self._response.headers

    def raise_for_status(self) -> None:
        """Raise HttpStatusError for 4xx/5xx responses."""
        try:
            self._response.raise_for_status()
        except httpx2.HTTPStatusError as e:
            raise HttpStatusError(response=self) from e

    def json(self) -> Any:  # noqa: ANN401
        """Parse response body as JSON."""
        return self._response.json()


class Httpx2SyncAdapter:
    """Synchronous HTTP adapter backed by httpx2.Client."""

    def __init__(self, client: httpx2.Client) -> None:
        """Initialize with an httpx2 sync client."""
        self._client = client

    def post(
        self,
        url: str,
        *,
        files: dict[str, tuple[str, IO[bytes], str]],
        headers: dict[str, str],
    ) -> ResponseProtocol:
        """Perform a POST request with multipart file upload."""
        return Httpx2ResponseAdapter(self._client.post(url, files=files, headers=headers))

    def put(
        self,
        url: str,
        *,
        content: bytes | IO[bytes],
        headers: dict[str, str],
    ) -> ResponseProtocol:
        """Perform a PUT request with raw byte content, or stream an open file."""
        body = content if isinstance(content, bytes) else iter_file(content)
        return Httpx2ResponseAdapter(self._client.put(url, content=body, headers=headers))

    def close(self) -> None:
        """Close the underlying httpx2 client."""
        self._client.close()


class Httpx2AsyncAdapter:
    """Asynchronous HTTP adapter backed by httpx2.AsyncClient."""

    def __init__(self, client: httpx2.AsyncClient) -> None:
        """Initialize with an httpx2 async client."""
        self._client = client

    async def post(
        self,
        url: str,
        *,
        files: dict[str, tuple[str, IO[bytes], str]],
        headers: dict[str, str],
    ) -> ResponseProtocol:
        """Perform an async POST request with multipart file upload."""
        return Httpx2ResponseAdapter(await self._client.post(url, files=files, headers=headers))

    async def put(
        self,
        url: str,
        *,
        content: bytes | IO[bytes],
        headers: dict[str, str],
    ) -> ResponseProtocol:
        """Perform an async PUT request with raw byte content, or stream an open file."""
        body = content if isinstance(content, bytes) else aiter_file(content)
        return Httpx2ResponseAdapter(await self._client.put(url, content=body, headers=headers))

    async def aclose(self) -> None:
        """Close the underlying httpx2 async client."""
        await self._client.aclose()
