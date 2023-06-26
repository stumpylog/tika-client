import logging
import urllib.parse
from pathlib import Path
from typing import Dict

from httpx import Client

from tika_client._constants import MIN_COMPRESS_LEN
from tika_client._types import MimeType
from tika_client._types import RequestContent
from tika_client.data_models import TikaResponse

logger = logging.getLogger("tika-client.utils")


class BaseResource:
    def __init__(self, client: Client, *, compress: bool) -> None:
        self.client = client
        self.compress = compress

    def _put_multipart(self, endpoint: str, filepath: Path, mime_type: MimeType = None) -> Dict:
        """
        Given an endpoint, file and an optional mime type, does a multi-part form
        data upload of the file to the end point.

        Returns the JSON response of the server
        """
        with filepath.open("rb") as handle:
            if mime_type is not None:
                files = {"upload-file": (filepath.name, handle, mime_type)}
            else:
                files = {"upload-file": (filepath.name, handle)}  # type: ignore
            try:
                # Filename is valid ASCII, use it
                filepath.name.encode("ascii")
                content_header = {"Content-Disposition": f"attachment; filename={filepath.name}"}
            except UnicodeEncodeError:
                # Ignore non-ascii, in case RFC 5987 is not supported, but also encode it
                filename_safed = filepath.name.encode("ascii", "ignore").decode("ascii")
                filepath_quoted = urllib.parse.quote(filepath.name, encoding="utf-8")
                content_header = {
                    "Content-Disposition": f"attachment; filename={filename_safed}; filename*=UTF-8''{filepath_quoted}",
                }

            resp = self.client.post(endpoint, files=files, headers=content_header)
            resp.raise_for_status()
            # Always JSON
            return resp.json()

    def _put_content(self, endpoint: str, content: RequestContent, mime_type: MimeType = None) -> Dict:
        """
        Give, an endpoint, content and optional mime type, does an HTTP PUT with the given content.

        Returns the JSON response of the server
        """
        content_bytes = content.encode("utf-8") if isinstance(content, str) else content
        content_length = len(content_bytes)
        headers = {}
        if self.compress and content_length > MIN_COMPRESS_LEN:
            from gzip import compress

            content_bytes = compress(content_bytes)
            content_length = len(content_bytes)
            headers["Content-Encoding"] = "gzip"

        headers["Content-Length"] = str(content_length)
        if mime_type is not None:
            headers["Content-Type"] = mime_type

        resp = self.client.put(endpoint, content=content_bytes, headers=headers)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _decoded_response(resp_json: Dict):
        """
        If possible, returns a more detailed class with properties that appear often in this
        mime type.  Otherwise, it's a basically raw data response, but with some helpers
        for processing fields into Python types
        """
        return TikaResponse(resp_json)
