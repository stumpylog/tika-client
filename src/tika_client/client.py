# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from httpx import Client

from tika_client._resource_meta import Metadata
from tika_client._resource_recursive import Recursive
from tika_client._resource_tika import Tika

if TYPE_CHECKING:
    from types import TracebackType

    from tika_client._types import Self


class TikaClient:
    def __init__(
        self,
        *,
        tika_url: str,
        timeout: float = 30.0,
        log_level: int = logging.ERROR,
        compress: bool = False,
    ):
        # Configure the client
        self._client = Client(base_url=tika_url, timeout=timeout)

        # Set the log level
        logging.getLogger("httpx").setLevel(log_level)
        logging.getLogger("httpcore").setLevel(log_level)

        # Only JSON responses supported
        self._client.headers.update({"Accept": "application/json"})

        if compress:
            self._client.headers.update({"Accept-Encoding": "gzip"})

        # Add the resources
        self.metadata = Metadata(self._client, compress=compress)
        self.tika = Tika(self._client, compress=compress)
        self.rmeta = Recursive(self._client, compress=compress)

    def add_headers(self, header: dict[str, str]) -> None:  # pragma: no cover
        """
        Updates the httpx Client headers with the given values
        """
        self._client.headers.update(header)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._client.close()
