# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import re
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from enum import Enum
from typing import Any

# Based on https://cwiki.apache.org/confluence/display/TIKA/Metadata+Overview

_TIME_RE = re.compile(
    r"(?P<year>\d{4})-"
    r"(?P<month>\d{2})-"
    r"(?P<day>\d{2})"
    r"[ tT]"
    r"(?P<hour>\d{2}):"
    r"(?P<minute>\d{2}):"
    r"(?P<second>\d{2})"
    r"(?P<fractional_seconds>\.\d+)?"
    r"(?P<timezone>[zZ]|[+-]\d{2}:\d{2})?",
)


class TikaKey(str, Enum):
    """
    Keys for access to certain Tika returned values in the JSON.

    Based on
      - https://cwiki.apache.org/confluence/pages/viewpage.action?pageId=235835139#MetadataOverview-TikaProcess
      - https://cwiki.apache.org/confluence/pages/viewpage.action?pageId=235835139#MetadataOverview-TikaGeneral
    """

    Parsers = "X-TIKA:Parsed-By"
    Parser_Full = "X-TIKA:Parsed-By-Full-Set"
    Parse_Time = "X-TIKA:parse_time_millis"
    ContentType = "Content-Type"
    ContentLength = "Content-Length"
    Content = "X-TIKA:content"


class DublinCoreKey(str, Enum):
    """
    Dublin Core keys for access to certain Tika returned values in the JSON.

    Based on:
      - https://cwiki.apache.org/confluence/pages/viewpage.action?pageId=235835139#MetadataOverview-DublinCore
    """

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
    """
    XMP keys for access to certain Tika returned values in the JSON.

    Based on:
      - https://cwiki.apache.org/confluence/pages/viewpage.action?pageId=235835139#MetadataOverview-XMP(eXtensibleMetadataPlatform)
    """

    About = "xmp:About"
    Created = "xmp:CreateDate"
    NumPages = "xmpTPg:NPages"


class OtherTikaKeys(str, Enum):
    """Other keys Tika may return in the JSON."""

    CharacterCount = "meta:character-count"
    LastAuthor = "meta:last-author"
    Revision = "cp:revision"
    Language = "language"


class TikaResponse:
    """
    A basic wrapper class for the JSON data returned from the Tika server.

    It sets fields which the response always appears to have, and some small helpers for getting and converting
    other data types, including handling the chance those don't exist in the response.

    All returned data is available in the decoded JSON form under the .data attribute
    """

    def __init__(self, data: dict[str | TikaKey | DublinCoreKey | XmpKey | OtherTikaKeys, Any]) -> None:
        """Construct a TikaResponse using the provided JSON data from a Tika server."""
        self.data = data

        # Always set keys
        self.type: str = self.data[TikaKey.ContentType]
        self.parsers: list[str] = self.data[TikaKey.Parsers]

        # Tika keys
        self.content: str | None = data.get(TikaKey.Content)
        self.content_length: int | None = int(self.data.get(TikaKey.ContentLength, "0")) or None

        # Dublin Core keys
        self.created: datetime | None = self.parse_datetime_string(self.data.get(DublinCoreKey.Created))
        self.modified: datetime | None = self.parse_datetime_string(self.data.get(DublinCoreKey.Modified))
        self.title: str | None = self.data.get(DublinCoreKey.Title)

        # Xmp keys
        self.xmp_created: datetime | None = self.parse_datetime_string(self.data.get(XmpKey.Created))
        self.page_count: int | None = int(self.data.get(XmpKey.NumPages, "0")) or None

        # Other general keys
        self.character_count: int | None = int(self.data.get(OtherTikaKeys.CharacterCount, "0")) or None
        self.revision: int | None = int(self.data.get(OtherTikaKeys.Revision, "0")) or None
        self.language: str | None = self.data.get(OtherTikaKeys.Language)
        self.last_author: str | None = self.data.get(OtherTikaKeys.LastAuthor)

    @staticmethod
    def parse_datetime_string(
        date_str: str | None,
    ) -> datetime | None:
        """
        If present, attempts to parse the given key as an ISO-8061 format datetime, including timezone handling.

        If not present, return None
        """
        if not date_str:
            return None

        m = _TIME_RE.match(date_str)
        if not m:
            return None

        (year, month, day, hour, minute, second, frac_sec, timezone_str) = m.groups()

        # Parse fractional seconds without float conversion to avoid precision loss
        if frac_sec is not None:
            # Remove the leading dot and pad/truncate to 6 digits
            frac_str = frac_sec[1:]  # Remove the '.'
            frac_str = frac_str.ljust(6, "0")[:6]  # Pad with zeros or truncate to 6 digits
            microseconds = int(frac_str)
        else:
            microseconds = 0

        tzinfo = None
        if timezone_str is not None:
            if timezone_str.lower() == "z":
                tzinfo = timezone.utc
            else:
                multi = -1 if timezone_str[0:1] == "-" else 1
                hours = int(timezone_str[1:3])
                minutes = int(timezone_str[4:])
                delta = timedelta(hours=hours, minutes=minutes) * multi
                tzinfo = timezone(delta)

        return datetime(
            year=int(year),
            month=int(month),
            day=int(day),
            hour=int(hour),
            minute=int(minute),
            second=int(second),
            microsecond=microseconds,
            tzinfo=tzinfo,
        )

    def __repr__(self) -> str:  # pragma: no cover
        """Representation of this class."""
        return f"{self.type} response"
