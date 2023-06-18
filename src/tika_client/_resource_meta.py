from pathlib import Path
from typing import Final

from tika_client._types import MimeType
from tika_client._utils import BaseResource


class Metadata(BaseResource):
    """
    Handles interaction with the /meta endpoint of a Tika
    server REST API.

    See documentation:
    https://cwiki.apache.org/confluence/display/TIKA/TikaServer#TikaServer-MetadataResource
    """

    ENDPOINT: Final[str] = "/meta"
    MULTI_PART_ENDPOINT = f"{ENDPOINT}/form"

    def from_file(self, filepath: Path, mime_type: MimeType = None):
        """
        PUTs the provided document to the metadata endpoint using multipart
        file encoding.  Optionally can provide the mime type
        """
        resp = self._put_multipart(self.MULTI_PART_ENDPOINT, filepath, mime_type)
        return self._decoded_response(resp)
