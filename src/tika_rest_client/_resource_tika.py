from pathlib import Path
from typing import Final
from typing import Optional

from tika_rest_client.utils import BaseResource
from tika_rest_client.utils import BaseResponse


class DocumentData(BaseResponse):
    def __post_init__(self) -> None:
        # TODO
        pass


class Tika(BaseResource):
    """
    Handles interaction with the /tika endpoint of a Tika
    server REST API.

    See documentation:
    https://cwiki.apache.org/confluence/display/TIKA/TikaServer#TikaServer-TikaResource
    """

    ENDPOINT: Final[str] = "/tika"
    MULTI_PART_ENDPOINT = f"{ENDPOINT}/form"

    def from_file(self, filepath: Path, mime_type: Optional[str] = None) -> DocumentData:
        """
        PUTs the provided document to the Tika endpoint using multipart
        file encoding.  Optionally can provide the mime type
        """
        return DocumentData(self.put_multipart(self.MULTI_PART_ENDPOINT, filepath, mime_type))
