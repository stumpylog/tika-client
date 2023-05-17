from http import HTTPStatus
from pathlib import Path
from typing import Final

from httpx import Client

from tika_rest_client.errors import RestHttpError


class DocumentMetadata:
    def __init__(self, json: dict) -> None:
        from pprint import pprint

        pprint(json)


class Metadata:
    """
    Handles interaction with the /meta endpoint of a Tika
    server REST API.

    See documentation:
    https://cwiki.apache.org/confluence/display/TIKA/TikaServer#TikaServer-MetadataResource
    """

    ENDPOINT: Final[str] = "/meta"

    def __init__(self, client: Client) -> None:
        self.client = client

    def from_file(self, filepath: Path, mime_type: str | None = None):
        """
        PUTs the provided document to the metadata endpoint using multipart
        file encoding.  Optionally can provide the mime type
        """
        with filepath.open("rb") as handle:
            if mime_type is not None:
                files = {"upload-file": (filepath.name, handle, mime_type)}
            else:
                files = {"upload-file": (filepath.name, handle)}
            resp = self.client.put(self.ENDPOINT, files=files)
            if resp.status_code != HTTPStatus.OK:
                raise RestHttpError(resp.status_code)
            return DocumentMetadata(resp.json())
