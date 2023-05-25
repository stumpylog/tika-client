from pathlib import Path
from typing import Final
from typing import Optional
from typing import Union

from httpx import Client

from tika_client._utils import BaseResource
from tika_client.data_models import KNOWN_DATA_TYPES
from tika_client.data_models import BaseResponse
from tika_client.data_models import Document


class _TikaBase(BaseResource):
    def _common_call(
        self,
        endpoint: str,
        filepath: Path,
        mime_type: Optional[str] = None,
    ) -> Union[BaseResponse, Document]:
        """
        Given a specific endpoint and a file, do a multipart put to the endpoint
        """
        resp = self.put_multipart(endpoint, filepath, mime_type)
        base_resp = BaseResponse(resp)
        if base_resp.type in KNOWN_DATA_TYPES:
            return KNOWN_DATA_TYPES[base_resp.type](base_resp.data)
        return base_resp  # pragma: no cover


class _TikaHtml(_TikaBase):
    ENDPOINT: Final[str] = "/tika"
    MULTI_PART_ENDPOINT = "/tika/form"

    def parse(self, filepath: Path, mime_type: Optional[str] = None):
        """
        Returns the formatted (as HTML) document data
        """
        return self._common_call(self.MULTI_PART_ENDPOINT, filepath, mime_type)


class _TikaPlain(_TikaBase):
    PLAIN_TEXT_CONTENT: Final[str] = "/tika/text"
    MULTI_PART_PLAIN_TEXT_CONTENT = "/tika/form/text"

    def parse(self, filepath: Path, mime_type: Optional[str] = None):
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
        self.text = _TikaPlain(self.client)
