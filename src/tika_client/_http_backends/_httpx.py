# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import IO
from typing import TYPE_CHECKING
from typing import Any

import httpx
from anyio.to_thread import run_sync

from tika_client.exceptions import HttpStatusError

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from collections.abc import Iterator

    from tika_client._http_backends._protocols import ResponseProtocol


# httpx will not take an open file as a request body: the sync client hangs on one and the
# async client rejects it outright. Both accept an iterator of chunks, which is how a file is
# streamed without being read into memory.
_STREAM_CHUNK_SIZE = 64 * 1024


def _iter_file(body: IO[bytes]) -> Iterator[bytes]:
    """Yield the file in chunks for httpx's sync client."""
    while chunk := body.read(_STREAM_CHUNK_SIZE):
        yield chunk


async def _aiter_file(body: IO[bytes]) -> AsyncIterator[bytes]:
    """Yield the file in chunks for httpx's async client, reading off the event loop."""
    while chunk := await run_sync(body.read, _STREAM_CHUNK_SIZE):
        yield chunk


class HttpxResponseAdapter:
    """Wraps an httpx.Response to satisfy ResponseProtocol."""

    def __init__(self, response: httpx.Response) -> None:
        """Initialize with an httpx response."""
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
    def headers(self) -> httpx.Headers:
        """Response headers."""
        return self._response.headers

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
        content: bytes | IO[bytes],
        headers: dict[str, str],
    ) -> ResponseProtocol:
        """Perform a PUT request with raw byte content, or stream an open file."""
        body = content if isinstance(content, bytes) else _iter_file(content)
        return HttpxResponseAdapter(self._client.put(url, content=body, headers=headers))

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
        content: bytes | IO[bytes],
        headers: dict[str, str],
    ) -> ResponseProtocol:
        """Perform an async PUT request with raw byte content, or stream an open file."""
        body = content if isinstance(content, bytes) else _aiter_file(content)
        return HttpxResponseAdapter(await self._client.put(url, content=body, headers=headers))

    async def aclose(self) -> None:
        """Close the underlying httpx async client."""
        await self._client.aclose()
