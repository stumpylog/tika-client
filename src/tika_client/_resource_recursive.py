# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

from tika_client._base import AsyncResource
from tika_client._base import SyncResource

if TYPE_CHECKING:
    from pathlib import Path

    from httpx import AsyncClient
    from httpx import Client

    from tika_client.data_models import TikaResponse

HTML_ENDPOINT: Final[str] = "/rmeta"
HTML_MULTI_PART_ENDPOINT: Final[str] = "/rmeta/form/html"
PLAIN_TEXT_ENDPOINT: Final[str] = "/rmeta/text"
PLAIN_TEXT_MULTI_PART_ENDPOINT: Final[str] = "/rmeta/form/text"


class SyncTikaRmetaBase(SyncResource):
    def common_call(
        self,
        endpoint: str,
        filepath: Path,
        mime_type: str | None = None,
    ) -> list[TikaResponse]:
        """
        Given a specific endpoint and a file, do a multipart put to the endpoint.

        Args:
            endpoint: The endpoint to send the file to
            filepath: The path to the file to send
            mime_type: The mime type of the file to send

        Returns:
            A list of JSON responses from the Tika server
        """
        return [self.decoded_response(item) for item in self.put_multipart(endpoint, filepath, mime_type)]


class SyncRecursiveMetaHtml(SyncTikaRmetaBase):
    def from_file(self, filepath: Path, mime_type: str | None = None) -> list[TikaResponse]:
        """
        Returns the formatted (as HTML) document data.

        Args:
            filepath: The path to the file to be sent to the Tika server
            mime_type: The mime type of the file to be sent to the Tika server

        Returns:
            A list of JSON responses from the Tika server
        """
        return self.common_call(HTML_MULTI_PART_ENDPOINT, filepath, mime_type)


class SyncRecursiveMetaPlain(SyncTikaRmetaBase):
    def from_file(self, filepath: Path, mime_type: str | None = None) -> list[TikaResponse]:
        """
        Returns the plain text document data.

        Args:
            filepath: The path to the file to be sent to the Tika server
            mime_type: The mime type of the file to be sent to the Tika server

        Returns:
            A list of JSON responses from the Tika server
        """
        return self.common_call(PLAIN_TEXT_MULTI_PART_ENDPOINT, filepath, mime_type)


class SyncRecursive(SyncResource):
    """
    Handles interaction with the /rmeta endpoint of a Tika server REST API, returning the HTML
    formatted content or the plain text, depending on how the client is accessed

    See documentation:
    https://cwiki.apache.org/confluence/display/TIKA/TikaServer#TikaServer-RecursiveMetadataandContent
    """

    def __init__(self, client: Client, *, compress: bool) -> None:
        super().__init__(client, compress=compress)
        # No support for XML endpoint.  Who wants that?
        self.as_html = SyncRecursiveMetaHtml(self.client, compress=compress)
        self.as_text = SyncRecursiveMetaPlain(self.client, compress=compress)


class AsyncTikaRmetaBase(AsyncResource):
    async def common_call(
        self,
        endpoint: str,
        filepath: Path,
        mime_type: str | None = None,
    ) -> list[TikaResponse]:
        """
        Given a specific endpoint and a file, do a multipart put to the endpoint.

        Args:
            endpoint: The endpoint to send the file to
            filepath: The path to the file to send
            mime_type: The mime type of the file to send

        Returns:
            A list of JSON responses from the Tika server
        """
        return [self.decoded_response(item) for item in await self.put_multipart(endpoint, filepath, mime_type)]


class AsyncRecursiveMetaHtml(AsyncTikaRmetaBase):
    async def from_file(self, filepath: Path, mime_type: str | None = None) -> list[TikaResponse]:
        """
        Returns the formatted (as HTML) document data

        Args:
            filepath: The path to the file to be sent to the Tika server
            mime_type: The mime type of the file to be sent to the Tika server

        Returns:
            A list of JSON responses from the Tika server
        """
        return await self.common_call(HTML_MULTI_PART_ENDPOINT, filepath, mime_type)


class AsyncRecursiveMetaPlain(AsyncTikaRmetaBase):
    async def from_file(self, filepath: Path, mime_type: str | None = None) -> list[TikaResponse]:
        """
        Returns the plain text document data.

        Args:
            filepath: The path to the file to be sent to the Tika server
            mime_type: The mime type of the file to be sent to the Tika server

        Returns:
            A list of JSON responses from the Tika server
        """
        return await self.common_call(PLAIN_TEXT_MULTI_PART_ENDPOINT, filepath, mime_type)


class AsyncRecursive(AsyncResource):
    """
    Handles interaction with the /rmeta endpoint of a Tika server REST API, returning the HTML
    formatted content or the plain text, depending on how the client is accessed

    See documentation:
    https://cwiki.apache.org/confluence/display/TIKA/TikaServer#TikaServer-RecursiveMetadataandContent
    """

    def __init__(self, client: AsyncClient, *, compress: bool) -> None:
        super().__init__(client, compress=compress)
        # No support for XML endpoint.  Who wants that?
        self.as_html = AsyncRecursiveMetaHtml(self.client, compress=compress)
        self.as_text = AsyncRecursiveMetaPlain(self.client, compress=compress)
