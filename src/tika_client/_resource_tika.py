# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

from tika_client._base import AsyncResource
from tika_client._base import SyncResource

PLAIN_TEXT_ENDPOINT: Final[str] = "/tika/text"
PLAIN_TEXT_MULTI_PART_ENDPOINT: Final[str] = "/tika/form/text"
HTML_ENDPOINT: Final[str] = "/tika"
HTML_MULTI_PART_ENDPOINT: Final[str] = "/tika/form"

if TYPE_CHECKING:
    from pathlib import Path

    from httpx import AsyncClient
    from httpx import Client

    from tika_client.data_models import TikaResponse


class SyncTikaHtml(SyncResource):
    def from_file(self, filepath: Path, mime_type: str | None = None) -> TikaResponse:
        """
        Return the formatted (as HTML) document data.

        Args:
            filepath: The path to the file to be sent to the Tika server
            mime_type: The mime type of the file to be sent to the Tika server

        Returns:
            The JSON response from the Tika server

        """
        return self.decoded_response(self.put_multipart(HTML_MULTI_PART_ENDPOINT, filepath, mime_type))

    def from_buffer(self, content: str | bytes, mime_type: str | None = None) -> TikaResponse:
        """
        Return the HTML formatted document data from a given string of document content.

        Args:
            content: The content to be sent to the Tika server
            mime_type: The mime type of the content to be sent to the Tika server

        Returns:
            The JSON response from the Tika server

        """
        return self.decoded_response(self.put_content(HTML_ENDPOINT, content, mime_type))


class SyncTikaPlain(SyncResource):
    def from_file(self, filepath: Path, mime_type: str | None = None) -> TikaResponse:
        """
        Return the plain text document data.

        Args:
            filepath: The path to the file to be sent to the Tika server
            mime_type: The mime type of the file to be sent to the Tika server

        Returns:
            The JSON response from the Tika server

        """
        return self.decoded_response(self.put_multipart(PLAIN_TEXT_MULTI_PART_ENDPOINT, filepath, mime_type))

    def from_buffer(self, content: str | bytes, mime_type: str | None = None) -> TikaResponse:
        """
        Return the plain text document data from a given string of document content.

        Args:
            content: The content to be sent to the Tika server
            mime_type: The mime type of the content to be sent to the Tika server

        Returns:
            The JSON response from the

        """
        return self.decoded_response(self.put_content(PLAIN_TEXT_ENDPOINT, content, mime_type))


class SyncTika(SyncResource):
    """
    Handles interaction with the /tika endpoint of a Tika server REST API.

    See documentation:
    https://cwiki.apache.org/confluence/display/TIKA/TikaServer#TikaServer-TikaResource
    """

    def __init__(self, client: Client, *, compress: bool) -> None:
        super().__init__(client, compress=compress)
        self.as_html = SyncTikaHtml(self.client, compress=compress)
        self.as_text = SyncTikaPlain(self.client, compress=compress)


class AsyncTikaHtml(AsyncResource):
    async def from_file(self, filepath: Path, mime_type: str | None = None) -> TikaResponse:
        """
        Return the formatted (as HTML) document data.

        Args:
            filepath: The path to the file to be sent to the Tika server
            mime_type: The mime type of the file to be sent to the Tika server

        Returns:
            The JSON response from the Tika server

        """
        return self.decoded_response(await self.put_multipart(HTML_MULTI_PART_ENDPOINT, filepath, mime_type))

    async def from_buffer(self, content: str | bytes, mime_type: str | None = None) -> TikaResponse:
        """
        Return the HTML formatted document data from a given string of document content.

        Args:
            content: The content to be sent to the Tika server
            mime_type: The mime type of the content to be sent to the Tika server

        Returns:
            The JSON response from the Tika server

        """
        return self.decoded_response(await self.put_content(HTML_ENDPOINT, content, mime_type))


class AsyncTikaPlain(AsyncResource):
    async def from_file(self, filepath: Path, mime_type: str | None = None) -> TikaResponse:
        """
        Return the plain text document data.

        Args:
            filepath: The path to the file to be sent to the Tika server
            mime_type: The mime type of the file to be sent to the Tika server

        Returns:
            The JSON response from the Tika server

        """
        return self.decoded_response(await self.put_multipart(PLAIN_TEXT_MULTI_PART_ENDPOINT, filepath, mime_type))

    async def from_buffer(self, content: str | bytes, mime_type: str | None = None) -> TikaResponse:
        """
        Return the plain text document data from a given string of document content.

        Args:
            content: The content to be sent to the Tika server
            mime_type: The mime type of the content to be sent to the Tika server

        Returns:
            The JSON response from the

        """
        return self.decoded_response(await self.put_content(PLAIN_TEXT_ENDPOINT, content, mime_type))


class AsyncTika(AsyncResource):
    """
    Handles interaction with the /tika endpoint of a Tika server REST API.

    See documentation:
    https://cwiki.apache.org/confluence/display/TIKA/TikaServer#TikaServer-TikaResource
    """

    def __init__(self, client: AsyncClient, *, compress: bool) -> None:
        super().__init__(client, compress=compress)
        self.as_html = AsyncTikaHtml(self.client, compress=compress)
        self.as_text = AsyncTikaPlain(self.client, compress=compress)
