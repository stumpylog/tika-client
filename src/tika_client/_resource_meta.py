from pathlib import Path
from typing import Final
from typing import List
from typing import Optional

from tika_client.utils import BaseResource
from tika_client.utils import BaseResponse


class DocumentMetadata(BaseResponse):
    def __post_init__(self) -> None:
        self.size = self.get_optional_int("Content-Length")
        self.type: str = self.data["Content-Type"]
        self.parsers: List[str] = self.data["X-TIKA:Parsed-By"]
        self.language: str = self.data["language"]
        self.revision = self.get_optional_int("cp:revision")
        self.created = self.get_optional_datetime("dcterms:created")
        self.modified = self.get_optional_datetime("dcterms:modified")


class Metadata(BaseResource):
    """
    Handles interaction with the /meta endpoint of a Tika
    server REST API.

    See documentation:
    https://cwiki.apache.org/confluence/display/TIKA/TikaServer#TikaServer-MetadataResource
    """

    ENDPOINT: Final[str] = "/meta"
    MULTI_PART_ENDPOINT = f"{ENDPOINT}/form"

    def from_file(self, filepath: Path, mime_type: Optional[str] = None) -> DocumentMetadata:
        """
        PUTs the provided document to the metadata endpoint using multipart
        file encoding.  Optionally can provide the mime type
        """
        return DocumentMetadata(self.put_multipart(self.MULTI_PART_ENDPOINT, filepath, mime_type))
