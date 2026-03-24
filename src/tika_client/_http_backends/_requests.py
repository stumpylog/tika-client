# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import IO
from typing import TYPE_CHECKING
from typing import Any
from typing import cast

import requests
import requests.exceptions

from tika_client._http_backends._protocols import HttpStatusError

if TYPE_CHECKING:
    from tika_client._http_backends._protocols import ResponseProtocol


class RequestsResponseAdapter:
    """Wraps a requests.Response to satisfy ResponseProtocol."""

    def __init__(self, response: requests.Response) -> None:
        """Initialize with a requests response."""
        self._response = response

    @property
    def status_code(self) -> int:
        """HTTP status code."""
        return self._response.status_code

    def raise_for_status(self) -> None:
        """Raise HttpStatusError for 4xx/5xx responses."""
        try:
            self._response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise HttpStatusError(response=self) from e

    def json(self) -> Any:  # noqa: ANN401
        """Parse response body as JSON."""
        return self._response.json()


class RequestsSyncAdapter:
    """Synchronous HTTP adapter backed by requests.Session."""

    def __init__(self, session: requests.Session, base_url: str, timeout: float) -> None:
        """Initialize with a requests session, base URL, and timeout."""
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def _url(self, path: str) -> str:
        return self._base_url + path

    def post(
        self,
        url: str,
        *,
        files: dict[str, tuple[str, IO[bytes], str]],
        headers: dict[str, str],
    ) -> ResponseProtocol:
        """Perform a POST request with multipart file upload."""
        return RequestsResponseAdapter(
            self._session.post(self._url(url), files=cast("Any", files), headers=headers, timeout=self._timeout),
        )

    def put(
        self,
        url: str,
        *,
        content: bytes,
        headers: dict[str, str],
    ) -> ResponseProtocol:
        """Perform a PUT request with raw byte content."""
        # requests uses data= for raw bytes; httpx uses content=
        return RequestsResponseAdapter(
            self._session.put(self._url(url), data=content, headers=headers, timeout=self._timeout),
        )

    def close(self) -> None:
        """Close the underlying requests session."""
        self._session.close()
