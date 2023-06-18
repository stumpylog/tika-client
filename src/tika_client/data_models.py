from datetime import datetime
from enum import Enum
from typing import Dict
from typing import Final
from typing import List
from typing import Optional
from typing import Set
from typing import Union


class TikaKey(str, Enum):
    Parsers = "X-TIKA:Parsed-By"
    ContentType = "Content-Type"
    ContentLength = "Content-Length"
    Content = "X-TIKA:content"
    Created = "dcterms:created"
    Modified = "dcterms:modified"


class TikaResponse:
    """
    A basic response from the API.  It sets fields which the response
    always appears to have, and some small helpers for getting and converting
    other data types, including handling the chance those don't exist in the response.

    All returned data is available in the decoded JSON form under the .data attribute
    """

    def __init__(self, data: Dict) -> None:
        self.data = data
        self.type: str = self.data[TikaKey.ContentType]
        self.parsers: List[str] = self.data[TikaKey.Parsers]

    # Helpers

    def get_optional_int(self, key: Union[TikaKey, str]) -> Optional[int]:
        if key not in self.data:  # pragma: no cover
            return None
        return int(self.data[key])

    def get_optional_datetime(self, key: Union[TikaKey, str]) -> Optional[datetime]:
        """
        If present, attempts to parse the given key as an ISO-8061 format
        datetime, including timezone handling and return if.

        If not present, return None
        """
        if key not in self.data:  # pragma: no cover
            return None
        # Handle Zulu time as UTC
        return datetime.fromisoformat(self.data[key].replace("Z", "+00:00"))

    def get_optional_string(self, key: Union[TikaKey, str]) -> Optional[str]:
        if key not in self.data:
            return None
        return self.data[key]

    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.type} response"


class ParsedDocument(TikaResponse):
    """
    Properties which Tika seems to return for document like
    parsing
    """

    @property
    def content(self) -> Optional[str]:
        return self.get_optional_string(TikaKey.Content)

    @property
    def content_length(self) -> Optional[int]:
        return self.get_optional_int(TikaKey.ContentLength)

    @property
    def created(self) -> Optional[datetime]:
        return self.get_optional_datetime(TikaKey.Created)

    @property
    def modified(self) -> Optional[datetime]:
        return self.get_optional_datetime(TikaKey.Modified)

    @property
    def page_count(self) -> Optional[int]:
        return self.get_optional_int("xmpTPg:NPages")

    @property
    def character_count(self) -> Optional[int]:
        return self.get_optional_int("meta:character-count")

    @property
    def language(self) -> Optional[str]:
        return self.get_optional_string("language")

    @property
    def last_author(self) -> Optional[str]:
        return self.get_optional_string("meta:last-author")

    @property
    def revision(self) -> Optional[int]:
        return self.get_optional_int("cp:revision")


class ParsedImage(TikaResponse):
    """
    Properties which seem to be returned for image like
    parsing
    """


IMAGE_TYPES: Final[Set[str]] = {"image/png", "image/jpeg", "image/webp"}
DOCUMENT_TYPES: Final[Set[str]] = {
    "application/vnd.oasis.opendocument.text",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.oasis.opendocument.spreadsheet",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/msword",
}
