from http import HTTPStatus
from pathlib import Path
from typing import Final
from typing import List
from typing import Optional

from httpx import Client

from tika_rest_client.errors import RestHttpError
from tika_rest_client.utils import BaseResponse


class DocumentMetadata(BaseResponse):
    def __init__(self, data: dict) -> None:
        super().__init__(data)
        self.size = self.get_optional_int("Content-Length")
        self.type: str = self.data["Content-Type"]
        self.parsers: List[str] = self.data["X-TIKA:Parsed-By"]
        self.language: str = self.data["language"]
        self.revision = self.get_optional_int("cp:revision")
        self.created = self.get_optional_datetime("dcterms:created")
        self.modified = self.get_optional_datetime("dcterms:modified")


class Metadata:
    """
    Handles interaction with the /meta endpoint of a Tika
    server REST API.

    See documentation:
    https://cwiki.apache.org/confluence/display/TIKA/TikaServer#TikaServer-MetadataResource
    """

    ENDPOINT: Final[str] = "/meta"
    MULTI_PART_ENDPOINT = f"{ENDPOINT}/form"

    def __init__(self, client: Client) -> None:
        self.client = client

    def from_file(self, filepath: Path, mime_type: Optional[str] = None) -> DocumentMetadata:
        """
        PUTs the provided document to the metadata endpoint using multipart
        file encoding.  Optionally can provide the mime type
        """
        with filepath.open("rb") as handle:
            if mime_type is not None:
                files = {"upload-file": (filepath.name, handle, mime_type)}
            else:
                files = {"upload-file": (filepath.name, handle)}
            resp = self.client.post(self.MULTI_PART_ENDPOINT, files=files)
            if resp.status_code != HTTPStatus.OK:
                raise RestHttpError(resp.status_code)
            return DocumentMetadata(resp.json())
