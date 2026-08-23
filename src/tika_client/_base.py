# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import re
from abc import ABC
from abc import abstractmethod
from mimetypes import guess_type
from typing import TYPE_CHECKING
from typing import Any
from typing import Generic
from typing import TypeVar
from urllib.parse import quote

from anyio.to_thread import run_sync

from tika_client._constants import MIN_COMPRESS_LEN
from tika_client._http_backends._protocols import AsyncClientProtocol
from tika_client._http_backends._protocols import HttpStatusError
from tika_client._http_backends._protocols import SyncClientProtocol
from tika_client.data_models import TikaResponse
from tika_client.exceptions import raise_for_tika_status

if TYPE_CHECKING:
    from collections.abc import Coroutine
    from pathlib import Path


T = TypeVar("T", bound="SyncClientProtocol | AsyncClientProtocol")

# Matches C0 control characters (including CR/LF) and DEL, none of which are
# valid in an HTTP header value. httpx/niquests/requests all reject these at
# send time with an opaque, backend-specific error; raising here fails fast
# with a clear message instead.
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")


class BaseResource(ABC, Generic[T]):
    def __init__(self, client: T, *, compress: bool) -> None:
        self.client = client
        self.compress = compress

    @staticmethod
    def get_content_headers(filename: str, disposition: str = "attachment") -> dict[str, str]:
        """
        Given a filename, returns the attachment header.

        Args:
            filename: The filename to encode
            disposition: The disposition of the file, defaults to attachment

        Returns:
            The attachment header

        Raises:
            ValueError: If filename contains a control character, which is not valid in an
                HTTP header value.

        """
        if _CONTROL_CHAR_RE.search(filename):
            msg = f"Filename {filename!r} contains a control character and cannot be used in a header value"
            raise ValueError(msg)

        try:
            # Test if filename is ASCII
            filename.encode("ascii")
        except UnicodeEncodeError:
            # For non-ASCII, provide ASCII fallback and UTF-8 encoded version
            ascii_filename = filename.encode("ascii", "replace").decode("ascii")
            # Replace ? marks from replace encoding with underscore for better readability
            ascii_filename = ascii_filename.replace("?", "_")
            # Escape quotes in ASCII version
            ascii_filename = ascii_filename.replace('"', '\\"')
            # UTF-8 encode the original filename and percent-encode the bytes
            utf8_filename = quote(filename.encode("utf-8"))

            return {
                "Content-Disposition": f'{disposition}; filename="{ascii_filename}"; '
                f"filename*=UTF-8''{utf8_filename}",
            }
        else:
            # If ASCII, we still need to escape quotes
            escaped_filename = filename.replace('"', '\\"')
            return {
                "Content-Disposition": f'{disposition}; filename="{escaped_filename}"',
            }

    @abstractmethod
    def put_multipart(  # pragma: no cover
        self,
        endpoint: str,
        filepath: Path,
        mime_type: str | None = None,
    ) -> Any | Coroutine[Any, Any, Any]:  # noqa: ANN401
        """
        Given an endpoint, file and a mime type, does a multi-part form data upload of the file to the end point.

        Returns the JSON response of the server

        Args:
            endpoint: The endpoint to send the file to
            filepath: The path to the file to send
            mime_type: The mime type of the file to send, if it's not provided, it will be guessed

        Returns:
            The JSON response of the server

        """

    @abstractmethod
    def put_content(  # pragma: no cover
        self,
        endpoint: str,
        content: str | bytes,
        mime_type: str | None = None,
        filename: str | None = None,
    ) -> Any | Coroutine[Any, Any, Any]:  # noqa: ANN401
        """
        Give, an endpoint, content and optional mime type, does an HTTP PUT with the given content.

        Returns the JSON response of the server

        Args:
            endpoint: The endpoint to send the content to
            content: The content to send
            mime_type: The mime type of the content, if it's not provided, it will be guessed
            filename: If provided, sent as a Content-Disposition filename hint

        Returns:
            The JSON response of the server

        """

    @staticmethod
    def decoded_response(resp_json: dict[str, Any]) -> TikaResponse:
        """
        Return the decoded JSON from Tika with helpers for access.

        Args:
            resp_json: The JSON response from the server

        Returns:
            The decoded response

        """
        return TikaResponse(resp_json)


class SyncResource(BaseResource[SyncClientProtocol]):
    def put_multipart(
        self,
        endpoint: str,
        filepath: Path,
        mime_type: str | None = None,
    ) -> Any:  # noqa: ANN401
        """
        Given an endpoint, file and a mime type, does a multi-part form data upload of the file to the end point.

        Args:
            endpoint: The endpoint to send the file to
            filepath: The path to the file to send
            mime_type: The mime type of the file to send, if it's not provided, it will be guessed

        Returns:
            Returns the JSON response of the server

        """
        with filepath.open("rb") as handler:
            response = self.client.post(
                endpoint,
                files={
                    "upload-file": (
                        filepath.name,
                        handler,
                        mime_type or guess_type(filepath.name)[0] or "",
                    ),
                },
                headers=BaseResource.get_content_headers(filepath.name),
            )
        try:
            response.raise_for_status()
        except HttpStatusError as e:
            raise_for_tika_status(response, cause=e)
        return response.json()

    def put_content(
        self,
        endpoint: str,
        content: str | bytes,
        mime_type: str | None = None,
        filename: str | None = None,
    ) -> Any:  # noqa: ANN401
        """
        Give, an endpoint, content and optional mime type, does an HTTP PUT with the given content.

        Args:
            endpoint: The endpoint to send the content to
            content: The content to send
            mime_type: The mime type of the content, if it's not provided, it will be guessed
            filename: If provided, sent as a Content-Disposition filename hint

        Returns:
            Returns the JSON response of the server

        """
        content_bytes = content.encode() if isinstance(content, str) else content
        content_length = len(content_bytes)

        headers = dict(BaseResource.get_content_headers(filename)) if filename is not None else {}
        if self.compress and content_length > MIN_COMPRESS_LEN:
            from gzip import compress  # noqa: PLC0415

            content_bytes = compress(content_bytes)
            content_length = len(content_bytes)
            headers["Content-Encoding"] = "gzip"

        headers["Content-Length"] = str(content_length)
        if mime_type is not None:
            headers["Content-Type"] = mime_type

        response = self.client.put(endpoint, content=content_bytes, headers=headers)
        try:
            response.raise_for_status()
        except HttpStatusError as e:
            raise_for_tika_status(response, cause=e)
        return response.json()


class AsyncResource(BaseResource[AsyncClientProtocol]):
    async def put_multipart(
        self,
        endpoint: str,
        filepath: Path,
        mime_type: str | None = None,
    ) -> Any:  # noqa: ANN401
        """
        Given an endpoint, file and a mime type, does a multi-part form data upload of the file to the end point.

        Args:
            endpoint: The endpoint to send the file to
            filepath: The path to the file to send
            mime_type: The mime type of the file to send, if it's not provided, it will be guessed

        Returns:
            Returns the JSON response of the server

        """
        with filepath.open("rb") as handler:
            response = await self.client.post(
                endpoint,
                files={
                    "upload-file": (
                        filepath.name,
                        handler,
                        mime_type or guess_type(filepath.name)[0] or "",
                    ),
                },
                headers=self.get_content_headers(filepath.name),
            )
        try:
            response.raise_for_status()
        except HttpStatusError as e:
            raise_for_tika_status(response, cause=e)
        return response.json()

    async def put_content(
        self,
        endpoint: str,
        content: str | bytes,
        mime_type: str | None = None,
        filename: str | None = None,
    ) -> Any:  # noqa: ANN401
        """
        Give, an endpoint, content and optional mime type, does an HTTP PUT with the given content.

        Args:
            endpoint: The endpoint to send the content to
            content: The content to send
            mime_type: The mime type of the content, if it's not provided, it will be guessed
            filename: If provided, sent as a Content-Disposition filename hint

        Returns:
            Returns the JSON response of the server

        """
        content_bytes = content.encode() if isinstance(content, str) else content
        content_length = len(content_bytes)

        headers = dict(BaseResource.get_content_headers(filename)) if filename is not None else {}
        if self.compress and content_length > MIN_COMPRESS_LEN:
            from gzip import compress  # noqa: PLC0415

            content_bytes = await run_sync(compress, content_bytes)
            content_length = len(content_bytes)
            headers["Content-Encoding"] = "gzip"

        headers["Content-Length"] = str(content_length)
        if mime_type is not None:
            headers["Content-Type"] = mime_type

        response = await self.client.put(endpoint, content=content_bytes, headers=headers)
        try:
            response.raise_for_status()
        except HttpStatusError as e:
            raise_for_tika_status(response, cause=e)
        return response.json()
