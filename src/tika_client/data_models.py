# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import re
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from enum import StrEnum
from typing import Any

from tika_client.exceptions import TikaContainerParseError
from tika_client.exceptions import TikaEmbeddedParseError
from tika_client.exceptions import TikaParseError
from tika_client.exceptions import TikaParseErrorGroup

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


class TikaKey(StrEnum):
    """
    Keys for access to certain Tika returned values in the JSON.

    As of Tika 4.x, Tika-computed keys live under a single `tk:` prefix
    (kebab-case), replacing the scattered `X-TIKA:` prefix used in 3.x.
    Verified against a live Tika 4.0.0 server.
    """

    Parsers = "tk:parsed-by"
    Parser_Full = "tk:parsed-by-full-set"
    Parse_Time = "tk:parse-time-millis"
    ContentType = "Content-Type"
    ContentLength = "Content-Length"
    Content = "tk:content"
    ContainerException = "tk:exception:container-exception"
    EmbeddedException = "tk:exception:embedded-exception"
    TaskDeadlineReached = "tk:exception:task-deadline-reached"


class DublinCoreKey(StrEnum):
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


class XmpKey(StrEnum):
    """
    XMP keys for access to certain Tika returned values in the JSON.

    Based on:
      - https://cwiki.apache.org/confluence/pages/viewpage.action?pageId=235835139#MetadataOverview-XMP(eXtensibleMetadataPlatform)
    """

    About = "xmp:About"
    Created = "xmp:CreateDate"
    NumPages = "xmpTPg:NPages"


class OtherTikaKeys(StrEnum):
    """Other keys Tika may return in the JSON."""

    CharacterCount = "meta:character-count"
    LastAuthor = "meta:last-author"
    Revision = "cp:revision"


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
        # Absent on a failure payload, the same reason parsers below defaults. TikaParseError
        # .partial builds a response from exactly such a payload, so this cannot hard-index.
        self.type: str | None = self.data.get(TikaKey.ContentType)
        # Absent when Tika couldn't parse at all (e.g. a zero-byte file), even on an
        # otherwise-200 response with an embedded tk:exception:container-exception.
        self.parsers: list[str] = self.data.get(TikaKey.Parsers, [])

        # Tika keys
        self.content: str | None = data.get(TikaKey.Content)
        # Tika 4 reports parse failures in-band on a 200. The /tika path raises on a
        # container exception; here the failure is exposed so an /rmeta caller keeps the
        # entries that did parse.
        # Both are exposed: with a failed container the embedded detail is still in the
        # payload, and would otherwise only be reachable through .data.
        self.container_exception: str | None = data.get(TikaKey.ContainerException)
        self.embedded_exception: str | None = data.get(TikaKey.EmbeddedException)
        self.parse_exception: str | None = self.container_exception or self.embedded_exception
        # PARTIAL_TIMEOUT is a 200 carrying whatever was extracted before the deadline, so
        # this is a successful-but-incomplete parse rather than a failure.
        #
        # Presence is the signal, because the wire format is unconfirmed: the key was read
        # from TikaCoreProperties rather than observed on a live response, its two siblings
        # in the tk:exception: namespace carry stack traces rather than booleans, and Tika
        # metadata can be multi-valued. Matching only the literal "true" would fail closed
        # on any other shape, recreating the silent truncation this exists to prevent. An
        # explicit false is still honoured.
        deadline = data.get(TikaKey.TaskDeadlineReached)
        self.truncated: bool = deadline is not None and str(deadline).strip().lower() not in {"false", ""}
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
        self.last_author: str | None = self.data.get(OtherTikaKeys.LastAuthor)

    def raise_for_parse_status(self) -> None:
        """
        Raise if this document carries an in-band parse exception, otherwise return None.

        Mirrors httpx's raise_for_status: the response is returned either way, and the
        caller decides when a failure should become an exception.

        Note:
            Deadline truncation is deliberately not raised; check .truncated for that.

        Raises:
            TikaContainerParseError: The container parser failed, so nothing was extracted.
            TikaEmbeddedParseError: An embedded document failed while the container succeeded.

        """
        if self.container_exception is not None:
            raise TikaContainerParseError(data=self.data, detail=self.container_exception)
        if self.embedded_exception is not None:
            raise TikaEmbeddedParseError(data=self.data, detail=self.embedded_exception)

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
                tzinfo = UTC
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


class TikaResponseList(list["TikaResponse"]):
    """
    The list of documents returned by /rmeta, one entry per embedded document.

    A plain list of TikaResponse, plus a convenience for the common question of
    whether any document in the tree failed to parse.
    """

    @property
    def has_parse_errors(self) -> bool:
        """Whether any document in the response carries an in-band parse exception."""
        return any(response.parse_exception is not None for response in self)

    @property
    def truncated(self) -> bool:
        """
        Whether any document was cut short by the task deadline.

        Deliberately separate from has_parse_errors, since truncation is a successful but
        incomplete parse rather than a failure. Exposed at the list level because a caller
        guarding only on has_parse_errors would otherwise ingest truncated content without
        noticing, and any one of N embedded documents can be the truncated one.
        """
        return any(response.truncated for response in self)

    def raise_for_parse_status(self) -> None:
        """
        Raise a TikaParseErrorGroup covering every failed document, or return None if all parsed.

        A group rather than a single error because one /rmeta call can fail in several
        places at once, and reporting only the first would hide the rest.

        Note:
            Deadline truncation is deliberately not raised; check .truncated for that.

        Raises:
            TikaParseErrorGroup: Containing one TikaParseError per failed document.

        """
        errors: list[TikaParseError] = []
        for response in self:
            try:
                response.raise_for_parse_status()
            except TikaParseError as e:
                errors.append(e)
        if errors:
            msg = f"{len(errors)} of {len(self)} documents failed to parse"
            raise TikaParseErrorGroup(msg, errors)
