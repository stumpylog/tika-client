from pathlib import Path
from typing import Final
from typing import List
from typing import Optional

from httpx import Client

from tika_client.utils import BaseResource
from tika_client.utils import BaseResponse


class RecursiveDocumentData(BaseResponse):
    def __post_init__(self):
        self.type: str = self.data["Content-Type"]
        self.content: str = self.data["X-TIKA:content"]
        self.created = self.get_optional_datetime("dcterms:created")
        self.modified = self.get_optional_datetime("dcterms:modified")


class RecursiveData(BaseResponse):
    def __post_init__(self) -> None:
        self.documents: List[RecursiveDocumentData] = []
        for item in self.data:
            self.documents.append(RecursiveDocumentData(item))


class _TikaRmetaBase(BaseResource):
    def _common_call(self, endpoint: str, filepath: Path, mime_type: Optional[str] = None) -> RecursiveData:
        """
        Given a specific endpoint and a file, do a multipart put to the endpoint
        """
        return RecursiveData(self.put_multipart(endpoint, filepath, mime_type))


class _RecursiveMetaHtml(_TikaRmetaBase):
    ENDPOINT: Final[str] = "/rmeta"
    MULTI_PART_ENDPOINT = "/rmeta/form/html"

    def parse(self, filepath: Path, mime_type: Optional[str] = None) -> RecursiveData:
        """
        Returns the formatted (as HTML) document data
        """
        return self._common_call(self.MULTI_PART_ENDPOINT, filepath, mime_type)


class _RecursiveMetaPlain(_TikaRmetaBase):
    ENDPOINT: Final[str] = "/rmeta/text"
    MULTI_PART_ENDPOINT = "/rmeta/form/text"

    def parse(self, filepath: Path, mime_type: Optional[str] = None) -> RecursiveData:
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
