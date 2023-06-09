from datetime import datetime
from enum import Enum
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

# Based on https://cwiki.apache.org/confluence/display/TIKA/Metadata+Overview


class TikaKey(str, Enum):
    Parsers = "X-TIKA:Parsed-By"
    ContentType = "Content-Type"
    ContentLength = "Content-Length"
    Content = "X-TIKA:content"


class DublinCoreKey(str, Enum):
    Creator = "dc:creator"
    Created = "dcterms:created"
    Modified = "dcterms:modified"
    Rights = "dc:rights"
    Contributor = "dc:contributor"
    Title = "dc:title"
    Relation = "dc:relation"
    Type = "dc:type"
    Identifier = "dc:identifier"
    Publisher = "dc:publisher"
    Description = "dc:description"
    Subject = "dc:subject"
    Language = "dc:language"
    Format = "dc:format"


class XmpKey(str, Enum):
    About = "xmp:About"
    Created = "xmp:CreateDate"
    NumPages = "xmpTPg:NPages"


class OtherTikaKeys(str, Enum):
    CharacterCount = "meta:character-count"
    LastAuthor = "meta:last-author"
    Revision = "cp:revision"
    Language = "language"


class TikaResponse:
    """
    A basic response from the API.  It sets fields which the response
    always appears to have, and some small helpers for getting and converting
    other data types, including handling the chance those don't exist in the response.

    All returned data is available in the decoded JSON form under the .data attribute
    """

    def __init__(self, data: Dict) -> None:
        self.data = data
        # Always set keys
        self.type: str = self.data[TikaKey.ContentType]
        self.parsers: List[str] = self.data[TikaKey.Parsers]

        # Tika keys
        self.content = self.get_optional_string(TikaKey.Content)
        self.content_length = self.get_optional_int(TikaKey.ContentLength)

        # Dublin Core keys
        self.created = self.get_optional_datetime(DublinCoreKey.Created)
        self.modified = self.get_optional_datetime(DublinCoreKey.Modified)
        self.title = self.get_optional_string(DublinCoreKey.Title)

        # Xmp keys
        # TODO: Implement more of these
        self.xmp_created = self.get_optional_datetime(XmpKey.Created)
        self.page_count = self.get_optional_int(XmpKey.NumPages)

        # Other general keys
        self.character_count = self.get_optional_int(OtherTikaKeys.CharacterCount)
        self.revision = self.get_optional_int(OtherTikaKeys.Revision)
        self.language = self.get_optional_string(OtherTikaKeys.Language)
        self.last_author = self.get_optional_string(OtherTikaKeys.LastAuthor)

    # Helpers

    def get_optional_int(self, key: Union[TikaKey, DublinCoreKey, XmpKey, str]) -> Optional[int]:
        if key not in self.data:  # pragma: no cover
            return None
        return int(self.data[key])

    def get_optional_datetime(self, key: Union[TikaKey, DublinCoreKey, XmpKey, str]) -> Optional[datetime]:
        """
        If present, attempts to parse the given key as an ISO-8061 format
        datetime, including timezone handling and return if.

        If not present, return None
        """
        if key not in self.data:  # pragma: no cover
            return None
        # Handle Zulu time as UTC
        return datetime.fromisoformat(self.data[key].replace("Z", "+00:00"))

    def get_optional_string(self, key: Union[TikaKey, DublinCoreKey, XmpKey, str]) -> Optional[str]:
        if key not in self.data:
            return None
        return self.data[key]

    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.type} response"
