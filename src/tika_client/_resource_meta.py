from pathlib import Path
from typing import Final
from typing import Optional
from typing import Union

from tika_client._utils import BaseResource
from tika_client.data_models import BaseResponse
from tika_client.data_models import DocumentMetadata


class Metadata(BaseResource):
    """
    Handles interaction with the /meta endpoint of a Tika
    server REST API.

    See documentation:
    https://cwiki.apache.org/confluence/display/TIKA/TikaServer#TikaServer-MetadataResource
    """

    ENDPOINT: Final[str] = "/meta"
    MULTI_PART_ENDPOINT = f"{ENDPOINT}/form"

    def from_file(self, filepath: Path, mime_type: Optional[str] = None) -> Union[BaseResponse, DocumentMetadata]:
        """
        PUTs the provided document to the metadata endpoint using multipart
        file encoding.  Optionally can provide the mime type
        """
        resp = self.put_multipart(self.MULTI_PART_ENDPOINT, filepath, mime_type)
        return DocumentMetadata(resp)
