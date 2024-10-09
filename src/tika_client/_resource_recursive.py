# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

from tika_client._utils import BaseResource

if TYPE_CHECKING:
    from pathlib import Path

    from httpx import Client

    from tika_client._types import MimeType
    from tika_client.data_models import TikaResponse


class _TikaRmetaBase(BaseResource):
    def _common_call(
        self,
        endpoint: str,
        filepath: Path,
        mime_type: MimeType = None,
    ) -> list[TikaResponse]:
        """
        Given a specific endpoint and a file, do a multipart put to the endpoint
        """
        return [self._decoded_response(item) for item in self._put_multipart(endpoint, filepath, mime_type)]


class _RecursiveMetaHtml(_TikaRmetaBase):
    ENDPOINT: Final[str] = "/rmeta"
    MULTI_PART_ENDPOINT = "/rmeta/form/html"

    def from_file(self, filepath: Path, mime_type: MimeType = None):
        """
        Returns the formatted (as HTML) document data
        """
        return self._common_call(self.MULTI_PART_ENDPOINT, filepath, mime_type)


class _RecursiveMetaPlain(_TikaRmetaBase):
    ENDPOINT: Final[str] = "/rmeta/text"
    MULTI_PART_ENDPOINT = "/rmeta/form/text"

    def from_file(self, filepath: Path, mime_type: MimeType = None):
        """
        Returns the plain text document data
        """
        return self._common_call(self.MULTI_PART_ENDPOINT, filepath, mime_type)


class Recursive(BaseResource):
    """
    Handles interaction with the /rmeta endpoint of a Tika server REST API, returning the HTML
    formatted content or the plain text, depending on how the client is accessed

    See documentation:
    https://cwiki.apache.org/confluence/display/TIKA/TikaServer#TikaServer-RecursiveMetadataandContent
    """

    def __init__(self, client: Client, *, compress: bool) -> None:
        super().__init__(client, compress=compress)
        # No support for XML endpoint.  Who wants that?
        self.as_html = _RecursiveMetaHtml(self.client, compress=compress)
        self.as_text = _RecursiveMetaPlain(self.client, compress=compress)
