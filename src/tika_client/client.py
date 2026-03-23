# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import logging
from abc import ABC
from abc import abstractmethod
from contextlib import AbstractAsyncContextManager
from contextlib import AbstractContextManager
from functools import cached_property
from typing import TYPE_CHECKING
from typing import Generic
from typing import TypeVar

from tika_client.__about__ import __version__
from tika_client._base import AsyncResource
from tika_client._base import SyncResource
from tika_client._http_backends import BackendType
from tika_client._http_backends import make_async_client
from tika_client._http_backends import make_sync_client
from tika_client._http_backends._protocols import AsyncClientProtocol
from tika_client._http_backends._protocols import SyncClientProtocol
from tika_client._resource_meta import AsyncMetadata
from tika_client._resource_meta import SyncMetadata
from tika_client._resource_recursive import AsyncRecursive
from tika_client._resource_recursive import SyncRecursive
from tika_client._resource_tika import AsyncTika
from tika_client._resource_tika import SyncTika

if TYPE_CHECKING:
    from types import TracebackType

T = TypeVar("T", bound="SyncClientProtocol | AsyncClientProtocol")
R = TypeVar("R", bound="SyncResource | AsyncResource")


class BaseTikaClient(ABC, Generic[T, R]):
    """
    Base class for Tika clients.

    Args:
        tika_url: The URL of the Tika server
        user_agent: Value to send as the User-Agent header.  Defaults to tika-client/{version}
        timeout: The timeout for the HTTP request
        log_level: The logging level
        compress: Whether to compress the response
        backend: The HTTP backend to use. One of "httpx", "niquests", or "auto".

    """

    def __init__(  # noqa: PLR0913
        self,
        tika_url: str,
        user_agent: str = f"tika-client/{__version__}",
        *,
        timeout: float = 30.0,
        log_level: int = logging.ERROR,
        compress: bool = False,
        backend: BackendType = "auto",
    ) -> None:
        """Construct a Tika client with the specific server URL, timeout and compression."""
        self.tika_url = tika_url
        self.timeout = timeout
        self.log_level = log_level
        self.compress = compress
        self.user_agent = user_agent
        self.backend = backend

    @cached_property
    def _default_headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "User-Agent": self.user_agent}

        if self.compress:
            headers["Accept-Encoding"] = "gzip"

        return headers

    @property
    @abstractmethod
    def client(self) -> T:  # pragma: no cover  # noqa: D102
        pass

    @property
    @abstractmethod
    def metadata(self) -> R:  # pragma: no cover  # noqa: D102
        pass

    @property
    @abstractmethod
    def tika(self) -> R:  # pragma: no cover  # noqa: D102
        pass

    @property
    @abstractmethod
    def rmeta(self) -> R:  # pragma: no cover  # noqa: D102
        pass


class TikaClient(AbstractContextManager["TikaClient"], BaseTikaClient[SyncClientProtocol, SyncResource]):
    """A sync client to interface with a Tika server."""

    def __enter__(self) -> TikaClient:
        """Enter the TikaClient context."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the TikaClient context and perform cleanup."""
        self.client.close()

    @cached_property
    def client(self) -> SyncClientProtocol:
        """Create and return the client instance for this TikaClient."""
        return make_sync_client(
            backend=self.backend,
            base_url=self.tika_url,
            timeout=self.timeout,
            headers=self._default_headers,
            log_level=self.log_level,
        )

    @cached_property
    def metadata(self) -> SyncMetadata:
        """Access the Tika metadata route."""
        return SyncMetadata(self.client, compress=self.compress)

    @cached_property
    def tika(self) -> SyncTika:
        """Access the Tika tika route."""
        return SyncTika(self.client, compress=self.compress)

    @cached_property
    def rmeta(self) -> SyncRecursive:
        """Access the Tika recursive metadata route."""
        return SyncRecursive(self.client, compress=self.compress)


class AsyncTikaClient(
    AbstractAsyncContextManager["AsyncTikaClient"],
    BaseTikaClient[AsyncClientProtocol, AsyncResource],
):
    """An async client to interface with a Tika server."""

    async def __aenter__(self) -> AsyncTikaClient:
        """Enter the TikaClient context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the TikaClient context and perform cleanup."""
        await self.client.aclose()

    @cached_property
    def client(self) -> AsyncClientProtocol:
        """Create and return the client instance for this TikaClient."""
        return make_async_client(
            backend=self.backend,
            base_url=self.tika_url,
            timeout=self.timeout,
            headers=self._default_headers,
            log_level=self.log_level,
        )

    @cached_property
    def metadata(self) -> AsyncMetadata:
        """Access the Tika metadata route."""
        return AsyncMetadata(self.client, compress=self.compress)

    @cached_property
    def tika(self) -> AsyncTika:
        """Access the Tika tika route."""
        return AsyncTika(self.client, compress=self.compress)

    @cached_property
    def rmeta(self) -> AsyncRecursive:
        """Access the Tika recursive metadata route."""
        return AsyncRecursive(self.client, compress=self.compress)
