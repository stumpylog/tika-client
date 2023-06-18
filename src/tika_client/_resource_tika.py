from pathlib import Path
from typing import Final

from httpx import Client

from tika_client._types import MimeType
from tika_client._types import RequestContent
from tika_client._utils import BaseResource


class _TikaHtml(BaseResource):
    ENDPOINT: Final[str] = "/tika"
    MULTI_PART_ENDPOINT = "/tika/form"

    def from_file(self, filepath: Path, mime_type: MimeType = None):
        """
        Returns the formatted (as HTML) document data
        """
        return self._decoded_response(self._put_multipart(self.MULTI_PART_ENDPOINT, filepath, mime_type))

    def from_buffer(self, content: RequestContent, mime_type: MimeType = None):
        """
        Returns the HTML formatted document data from a given string of document content
        """
        return self._decoded_response(self._put_content(self.ENDPOINT, content, mime_type))


class _TikaPlain(BaseResource):
    PLAIN_TEXT_CONTENT: Final[str] = "/tika/text"
    MULTI_PART_PLAIN_TEXT_CONTENT = "/tika/form/text"

    def from_file(self, filepath: Path, mime_type: MimeType = None):
        """
        Returns the plain text document data
        """
        return self._decoded_response(self._put_multipart(self.MULTI_PART_PLAIN_TEXT_CONTENT, filepath, mime_type))

    def from_buffer(self, content: RequestContent, mime_type: MimeType = None):
        """
        Returns the plain text document data from a given string of document content
        """
        return self._decoded_response(self._put_content(self.PLAIN_TEXT_CONTENT, content, mime_type))


class Tika(BaseResource):
    """
    Handles interaction with the /tika endpoint of a Tika server REST API, returning the HTML
    formatted content or the plain text, depending on how the client is accessed

    See documentation:
    https://cwiki.apache.org/confluence/display/TIKA/TikaServer#TikaServer-TikaResource
    """

    def __init__(self, client: Client, *, compress: bool) -> None:
        super().__init__(client, compress=compress)
        self.as_html = _TikaHtml(self.client, compress=compress)
        self.as_text = _TikaPlain(self.client, compress=compress)
