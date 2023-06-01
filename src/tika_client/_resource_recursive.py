import logging
from pathlib import Path
from typing import Final
from typing import List
from typing import Optional
from typing import Union

from httpx import Client

from tika_client._utils import BaseResource
from tika_client.data_models import KNOWN_DATA_TYPES
from tika_client.data_models import BaseResponse
from tika_client.data_models import Document
from tika_client.data_models import Image

logger = logging.getLogger("tika-client.rmeta")


class _TikaRmetaBase(BaseResource):
    def _common_call(
        self,
        endpoint: str,
        filepath: Path,
        mime_type: Optional[str] = None,
    ) -> List[Union[Document, Image, BaseResponse]]:
        """
        Given a specific endpoint and a file, do a multipart put to the endpoint
        """
        documents: List[Union[Document, Image, BaseResponse]] = []
        for item in self.put_multipart(endpoint, filepath, mime_type):
            # If a detailed class exists, use it
            if item["Content-Type"] in KNOWN_DATA_TYPES:
                documents.append(KNOWN_DATA_TYPES[item["Content-Type"]](item))
            else:
                logger.warning(f"Unknown content-type: {item['Content-Type']}")
                documents.append(BaseResponse(item))
        return documents


class _RecursiveMetaHtml(_TikaRmetaBase):
    ENDPOINT: Final[str] = "/rmeta"
    MULTI_PART_ENDPOINT = "/rmeta/form/html"

    def from_file(self, filepath: Path, mime_type: Optional[str] = None):
        """
        Returns the formatted (as HTML) document data
        """
        return self._common_call(self.MULTI_PART_ENDPOINT, filepath, mime_type)


class _RecursiveMetaPlain(_TikaRmetaBase):
    ENDPOINT: Final[str] = "/rmeta/text"
    MULTI_PART_ENDPOINT = "/rmeta/form/text"

    def from_file(self, filepath: Path, mime_type: Optional[str] = None):
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

    def __init__(self, client: Client) -> None:
        super().__init__(client)
        # No support for XML endpoint.  Who wants that?
        self.html = _RecursiveMetaHtml(self.client)
        self.text = _RecursiveMetaPlain(self.client)
