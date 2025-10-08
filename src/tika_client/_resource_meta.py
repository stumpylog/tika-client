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

    from tika_client.data_models import TikaResponse

ENDPOINT: Final[str] = "/meta"
MULTI_PART_ENDPOINT: Final[str] = f"{ENDPOINT}/form"


class SyncMetadata(SyncResource):
    """
    Handles interaction with the /meta endpoint of a Tika server REST API.

    See documentation:
    https://cwiki.apache.org/confluence/display/TIKA/TikaServer#TikaServer-MetadataResource
    """

    def from_file(self, filepath: Path, mime_type: str | None = None) -> TikaResponse:
        """
        PUT the provided document to the metadata endpoint using multipart file encoding.

        Args:
            filepath: The path to the file to be sent to the Tika server
            mime_type: The mime type of the file to be sent to the Tika server

        Returns:
            The JSON response from the Tika server

        """
        resp = self.put_multipart(MULTI_PART_ENDPOINT, filepath, mime_type)
        return self.decoded_response(resp)


class AsyncMetadata(AsyncResource):
    """
    Handles interaction with the /meta endpoint of a Tika server REST API.

    See documentation:
    https://cwiki.apache.org/confluence/display/TIKA/TikaServer#TikaServer-MetadataResource
    """

    async def from_file(self, filepath: Path, mime_type: str | None = None) -> TikaResponse:
        """
        PUT the provided document to the metadata endpoint using multipart file encoding.

        Args:
            filepath: The path to the file to be sent to the Tika server
            mime_type: The mime type of the file to be sent to the Tika server

        Returns:
            The JSON response from the Tika server

        """
        resp = await self.put_multipart(MULTI_PART_ENDPOINT, filepath, mime_type)
        return self.decoded_response(resp)
