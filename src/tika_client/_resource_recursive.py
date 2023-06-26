import logging
from pathlib import Path
from typing import Final
from typing import List

from httpx import Client

from tika_client._types import MimeType
from tika_client._utils import BaseResource
from tika_client.data_models import TikaResponse

logger = logging.getLogger("tika-client.rmeta")


class _TikaRmetaBase(BaseResource):
    def _common_call(
        self,
        endpoint: str,
        filepath: Path,
        mime_type: MimeType = None,
    ) -> List[TikaResponse]:
        """
        Given a specific endpoint and a file, do a multipart put to the endpoint
        """
        documents: List[TikaResponse] = []
        for item in self._put_multipart(endpoint, filepath, mime_type):
            documents.append(self._decoded_response(item))
        return documents


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
