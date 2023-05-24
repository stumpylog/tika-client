from pathlib import Path
from typing import Final
from typing import List
from typing import Optional

from httpx import Client

from tika_client.utils import BaseResource
from tika_client.utils import BaseResponse


class DocumentData(BaseResponse):
    def __post_init__(self) -> None:
        self.size = self.get_optional_int("Content-Length")
        self.type: str = self.data["Content-Type"]
        self.parsers: List[str] = self.data["X-TIKA:Parsed-By"]
        self.content: str = self.data["X-TIKA:content"]


class _TikaBase(BaseResource):
    def _common_call(self, endpoint: str, filepath: Path, mime_type: Optional[str] = None) -> DocumentData:
        """
        Given a specific endpoint and a file, do a multipart put to the endpoint
        """
        return DocumentData(self.put_multipart(endpoint, filepath, mime_type))


class _TikaHtml(_TikaBase):
    ENDPOINT: Final[str] = "/tika"
    MULTI_PART_ENDPOINT = "/tika/form"

    def parse(self, filepath: Path, mime_type: Optional[str] = None) -> DocumentData:
        """
        Returns the formatted (as HTML) document data
        """
        return self._common_call(self.MULTI_PART_ENDPOINT, filepath, mime_type)


class _TikaPlain(_TikaBase):
    PLAIN_TEXT_CONTENT: Final[str] = "/tika/text"
    MULTI_PART_PLAIN_TEXT_CONTENT = "/tika/form/text"

    def parse(self, filepath: Path, mime_type: Optional[str] = None) -> DocumentData:
        """
        Returns the plain text document data
        """
        return self._common_call(self.MULTI_PART_PLAIN_TEXT_CONTENT, filepath, mime_type)


class Tika(BaseResource):
    """
    Handles interaction with the /tika endpoint of a Tika server REST API, returning the HTML
    formatted content or the plain text, depending on how the client is accessed

    See documentation:
    https://cwiki.apache.org/confluence/display/TIKA/TikaServer#TikaServer-TikaResource
    """

    def __init__(self, client: Client) -> None:
        super().__init__(client)
        self.html = _TikaHtml(self.client)
        self.plain = _TikaPlain(self.client)
