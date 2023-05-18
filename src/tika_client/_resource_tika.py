from pathlib import Path
from typing import Final
from typing import List
from typing import Optional

from tika_client.utils import BaseResource
from tika_client.utils import BaseResponse


class DocumentData(BaseResponse):
    def __post_init__(self) -> None:
        self.size = self.get_optional_int("Content-Length")
        self.type: str = self.data["Content-Type"]
        self.parsers: List[str] = self.data["X-TIKA:Parsed-By"]
        self.content: str = self.data["X-TIKA:content"]


class Tika(BaseResource):
    """
    Handles interaction with the /tika endpoint of a Tika
    server REST API.
    See documentation:
    https://cwiki.apache.org/confluence/display/TIKA/TikaServer#TikaServer-TikaResource
    """

    ENDPOINT: Final[str] = "/tika"
    PLAIN_TEXT_CONTENT: Final[str] = f"{ENDPOINT}/text"
    MULTI_PART_ENDPOINT = f"{ENDPOINT}/form"
    MULTI_PART_PLAIN_TEXT_CONTENT = f"{MULTI_PART_ENDPOINT}/text"

    def _common_call(self, endpoint: str, filepath: Path, mime_type: Optional[str] = None) -> DocumentData:
        return DocumentData(self.put_multipart(endpoint, filepath, mime_type))

    def parse_formatted(self, filepath: Path, mime_type: Optional[str] = None) -> DocumentData:
        """
        PUTs the provided document to the Tika endpoint using multipart
        file encoding.  Optionally can provide the mime type
        """
        return self._common_call(self.MULTI_PART_ENDPOINT, filepath, mime_type)

    def parse_plain(self, filepath: Path, mime_type: Optional[str] = None) -> DocumentData:
        return self._common_call(self.MULTI_PART_PLAIN_TEXT_CONTENT, filepath, mime_type)
