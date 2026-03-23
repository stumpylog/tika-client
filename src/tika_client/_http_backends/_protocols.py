# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import IO
from typing import Any
from typing import Protocol


class HttpStatusError(Exception):
    """Unified HTTP status error raised by all backends."""

    def __init__(self, *, response: ResponseProtocol) -> None:
        """Initialize the error with the response that caused it."""
        super().__init__()
        self.response = response


class ResponseProtocol(Protocol):
    """Protocol defining the interface for HTTP response objects."""

    @property
    def status_code(self) -> int:
        """HTTP status code of the response."""
        ...  # pragma: no cover

    def raise_for_status(self) -> None:
        """Raise HttpStatusError for 4xx/5xx responses."""
        ...  # pragma: no cover

    def json(self) -> Any:  # noqa: ANN401
        """Parse response body as JSON."""
        ...  # pragma: no cover


class SyncClientProtocol(Protocol):
    """Protocol defining the interface for synchronous HTTP clients."""

    def post(
        self,
        url: str,
        *,
        files: dict[str, tuple[str, IO[bytes], str]],
        headers: dict[str, str],
    ) -> ResponseProtocol:
        """Perform a POST request with multipart file upload."""
        ...  # pragma: no cover

    def put(
        self,
        url: str,
        *,
        content: bytes,
        headers: dict[str, str],
    ) -> ResponseProtocol:
        """Perform a PUT request with raw byte content."""
        ...  # pragma: no cover

    def close(self) -> None:
        """Close the client and release resources."""
        ...  # pragma: no cover


class AsyncClientProtocol(Protocol):
    """Protocol defining the interface for asynchronous HTTP clients."""

    async def post(
        self,
        url: str,
        *,
        files: dict[str, tuple[str, IO[bytes], str]],
        headers: dict[str, str],
    ) -> ResponseProtocol:
        """Perform an async POST request with multipart file upload."""
        ...  # pragma: no cover

    async def put(
        self,
        url: str,
        *,
        content: bytes,
        headers: dict[str, str],
    ) -> ResponseProtocol:
        """Perform an async PUT request with raw byte content."""
        ...  # pragma: no cover

    async def aclose(self) -> None:
        """Asynchronously close the client and release resources."""
        ...  # pragma: no cover
