from datetime import datetime
from typing import Dict
from typing import Final
from typing import List
from typing import Optional
from typing import Type
from typing import Union


class BaseResponse:
    """
    A basic response from the API.  It sets fields which the response
    always appears to have, and some small helpers for getting and converting
    other data types, including handling the chance those don't exist in the response.

    All returned data is available in the decoded JSON form under the .data attribute
    """

    def __init__(self, data: Dict) -> None:
        self.data = data
        self.type: str = self.data["Content-Type"]
        self.parsers: List[str] = self.data["X-TIKA:Parsed-By"]

    def get_optional_int(self, key: str) -> Optional[int]:
        if key not in self.data:  # pragma: no cover
            return None
        return int(self.data[key])

    def get_optional_datetime(self, key: str) -> Optional[datetime]:
        if key not in self.data:  # pragma: no cover
            return None
        # Handle Zulu time as UTC
        return datetime.fromisoformat(self.data[key].replace("Z", "+00:00"))

    def get_optional_string(self, key: str) -> Optional[str]:
        if key not in self.data:
            return None
        return self.data[key]

    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.type} response"


class DocumentMetadata(BaseResponse):
    """
    Basic metadata about a document, attempting to expand the basic response set
    with item such as revision and dates.
    """

    def __init__(self, data: Dict) -> None:
        super().__init__(data)
        self.size = self.get_optional_int("Content-Length")

        self.language = self.get_optional_string("language")

        self.revision = self.get_optional_int("cp:revision")

        self.created = self.get_optional_datetime("dcterms:created")
        self.modified = self.get_optional_datetime("dcterms:modified")


class Document(BaseResponse):

    """
    Response from the tika and rmeta end points.  Expands on the basic values
    for those which appear always or often set for common office document types.
    """

    def __init__(self, data: Dict) -> None:
        super().__init__(data)
        self.size = self.get_optional_int("Content-Length")
        self.content: str = self.data["X-TIKA:content"]
        self.metadata = DocumentMetadata(self.data)


class Image(BaseResponse):
    """
    Some recursive metadata calls will included embedded images, with
    lots of data, but none that looks really relevant
    """


# If a particular Content-Type has a better parsing class for it, map it here
KNOWN_DATA_TYPES: Final[Dict[str, Union[Type[Document], Type[Image]]]] = {
    "application/vnd.oasis.opendocument.text": Document,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": Document,
    "application/vnd.oasis.opendocument.spreadsheet": Document,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": Document,
    "image/png": Image,
}
