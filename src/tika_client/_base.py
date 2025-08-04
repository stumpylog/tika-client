# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from mimetypes import guess_type
from typing import TYPE_CHECKING
from typing import Any
from typing import Generic
from typing import TypeVar
from urllib.parse import quote

from anyio.to_thread import run_sync
from httpx import AsyncClient
from httpx import Client

from tika_client._constants import MIN_COMPRESS_LEN
from tika_client.data_models import TikaResponse

if TYPE_CHECKING:
    from collections.abc import Coroutine
    from pathlib import Path


T = TypeVar("T", bound="Client | AsyncClient")


class BaseResource(ABC, Generic[T]):
    def __init__(self, client: T, *, compress: bool) -> None:
        self.client = client
        self.compress = compress

    def get_content_headers(self, filename: str, disposition: str = "attachment") -> dict[str, str]:
        """
        Given a filename, returns the attachment header.

        Args:
            filename: The filename to encode
            disposition: The disposition of the file, defaults to attachment

        Returns:
            The attachment header
        """
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
    ) -> Any | Coroutine[Any, Any, Any]:
        """
        Given an endpoint, file and an optional mime type, does a multi-part form
        data upload of the file to the end point.

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
    ) -> Any | Coroutine[Any, Any, Any]:
        """
        Give, an endpoint, content and optional mime type, does an HTTP PUT with the given content.

        Returns the JSON response of the server

        Args:
            endpoint: The endpoint to send the content to
            content: The content to send
            mime_type: The mime type of the content, if it's not provided, it will be guessed

        Returns:
            The JSON response of the server
        """

    @staticmethod
    def decoded_response(resp_json: dict[str, Any]) -> TikaResponse:
        """
        If possible, returns a more detailed class with properties that appear often in this
        mime type.  Otherwise, it's a basically raw data response, but with some helpers
        for processing fields into Python types

        Args:
            resp_json: The JSON response from the server

        Returns:
            The decoded response
        """
        return TikaResponse(resp_json)


class SyncResource(BaseResource[Client]):
    def put_multipart(
        self,
        endpoint: str,
        filepath: Path,
        mime_type: str | None = None,
    ) -> Any:
        """
        Given an endpoint, file and an optional mime type, does a multi-part form
        data upload of the file to the end point.

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
                        mime_type if mime_type else guess_type(filepath.name)[0] or "",
                    ),
                },
                headers=self.get_content_headers(filepath.name),
            )
        response.raise_for_status()
        return response.json()

    def put_content(
        self,
        endpoint: str,
        content: str | bytes,
        mime_type: str | None = None,
    ) -> Any:
        """
        Give, an endpoint, content and optional mime type, does an HTTP PUT with the given content.

        Args:
            endpoint: The endpoint to send the content to
            content: The content to send
            mime_type: The mime type of the content, if it's not provided, it will be guessed

        Returns:
            Returns the JSON response of the server
        """
        content_bytes = content.encode() if isinstance(content, str) else content
        content_length = len(content_bytes)

        headers = {}
        if self.compress and content_length > MIN_COMPRESS_LEN:
            from gzip import compress  # noqa: PLC0415

            content_bytes = compress(content_bytes)
            content_length = len(content_bytes)
            headers["Content-Encoding"] = "gzip"

        headers["Content-Length"] = str(content_length)
        if mime_type is not None:
            headers["Content-Type"] = mime_type

        response = self.client.put(endpoint, content=content_bytes, headers=headers)
        response.raise_for_status()
        return response.json()


class AsyncResource(BaseResource[AsyncClient]):
    async def put_multipart(
        self,
        endpoint: str,
        filepath: Path,
        mime_type: str | None = None,
    ) -> Any:
        """
        Given an endpoint, file and an optional mime type, does a multi-part form
        data upload of the file to the end point.

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
                        mime_type if mime_type else guess_type(filepath.name)[0] or "",
                    ),
                },
                headers=self.get_content_headers(filepath.name),
            )
        response.raise_for_status()
        return response.json()

    async def put_content(
        self,
        endpoint: str,
        content: str | bytes,
        mime_type: str | None = None,
    ) -> Any:
        """
        Give, an endpoint, content and optional mime type, does an HTTP PUT with the given content.

        Args:
            endpoint: The endpoint to send the content to
            content: The content to send
            mime_type: The mime type of the content, if it's not provided, it will be guessed

        Returns:
            Returns the JSON response of the server
        """
        content_bytes = content.encode() if isinstance(content, str) else content
        content_length = len(content_bytes)

        headers = {}
        if self.compress and content_length > MIN_COMPRESS_LEN:
            from gzip import compress  # noqa: PLC0415

            content_bytes = await run_sync(compress, content_bytes)
            content_length = len(content_bytes)
            headers["Content-Encoding"] = "gzip"

        headers["Content-Length"] = str(content_length)
        if mime_type is not None:
            headers["Content-Type"] = mime_type

        response = await self.client.put(endpoint, content=content_bytes, headers=headers)
        response.raise_for_status()
        return response.json()
