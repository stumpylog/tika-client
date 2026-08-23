# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import json
import math
from typing import TYPE_CHECKING

from tika_client._http_backends._protocols import HttpStatusError

if TYPE_CHECKING:
    from tika_client._http_backends._protocols import ResponseProtocol


class TikaServerError(HttpStatusError):
    """
    Base class for the Tika 4.x tika-server error envelope.

    Tika 4's error bodies are inconsistent by design: some are JSON
    (`{"status": "...", "message": "..."}`), some are plain text, and some
    (422 partial-parse) are empty or raw partial content. This class never
    raises while parsing a response body - it degrades to `tika_status=None`,
    `message=None` whenever the body isn't the expected JSON shape.
    """

    def __init__(self, *, response: ResponseProtocol) -> None:
        """Build the error from a non-2xx response, parsing whatever body shape it has."""
        super().__init__(response=response)
        self.status_code = response.status_code
        self.response_text = response.text
        self.tika_status, self.message = _try_parse_status_envelope(response.text)
        self.retry_after = _parse_retry_after(response.headers)

    def __str__(self) -> str:
        """Render status_code, tika_status, and message for useful default log/traceback output."""
        parts = [f"HTTP {self.status_code}"]
        if self.tika_status:
            parts.append(f"tika_status={self.tika_status!r}")
        if self.message:
            parts.append(self.message)
        return " - ".join(parts)


class TikaTimeoutError(TikaServerError):
    """A response (typically 503) with tika_status == "TIMEOUT" - the fork exceeded its configured timeout."""


class TikaCrashError(TikaServerError):
    """A response (typically 503) with tika_status in {"UNSPECIFIED_CRASH", "OOM"} - the forked JVM crashed."""


class TikaSaturatedError(TikaServerError):
    """A 429 response - the fork pool is saturated; retry_after (if present) indicates a backoff hint."""


class TikaPayloadTooLargeError(TikaServerError):
    """
    A 413 response.

    Confirmed to have two distinct shapes: plain text when the request body exceeds
    maxRequestSizeBytes (tika_status will be None), or JSON PAYLOAD_LIMIT_EXCEEDED
    when the parse result exceeds the IPC payload limit.
    """


class TikaPartialParseError(TikaServerError):
    """
    A 422 response from a raw endpoint (e.g. /tika/html) - container-level parse exception.

    Confirmed never JSON in practice: the body is either empty or the raw
    partially-extracted content, so tika_status and message end up None in real usage.
    Nothing in this class enforces that - the base class still attempts to parse the
    envelope for every response - it is an observed property of Tika's behavior rather
    than a parsing rule, so callers should not treat those attributes as guaranteed None.
    """


def _try_parse_status_envelope(text: str) -> tuple[str | None, str | None]:
    if not text:
        return None, None
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError, RecursionError):
        # RecursionError: a deeply nested body (e.g. from a hostile or corrupt server)
        # can exceed Python's recursion limit during json.loads; this must degrade like
        # any other malformed body, never escape as an unhandled exception.
        return None, None
    if not isinstance(data, dict):
        return None, None
    status = data.get("status")
    message = data.get("message")
    return (
        status if isinstance(status, str) else None,
        message if isinstance(message, str) else None,
    )


def _parse_retry_after(headers: object) -> float | None:
    getter = getattr(headers, "get", None)
    if getter is None:
        return None
    value = getter("Retry-After")
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        # TypeError covers header mappings whose get() returns a non-str (e.g. a
        # list from a multi-value header mapping); constructing the error must never raise.
        return None
    if not math.isfinite(parsed) or parsed < 0:
        # A hostile or broken Retry-After ("inf", "nan", or negative) is not a usable
        # backoff hint - discard it rather than handing a caller's time.sleep() a value
        # that would hang forever or raise.
        return None
    return parsed


def raise_for_tika_status(response: ResponseProtocol, *, cause: BaseException | None = None) -> None:
    """
    Raise the appropriate TikaServerError subclass for a non-2xx response, or return if 2xx.

    Args:
        response: The response to inspect and potentially raise from.
        cause: The underlying backend exception (if any) to chain via `raise ... from cause`.

    """
    status_code = response.status_code
    if status_code < 400:  # noqa: PLR2004
        return

    if status_code == 422:  # noqa: PLR2004
        raise TikaPartialParseError(response=response) from cause

    tika_status, _ = _try_parse_status_envelope(response.text)

    if status_code == 429:  # noqa: PLR2004
        raise TikaSaturatedError(response=response) from cause
    if status_code == 413:  # noqa: PLR2004
        raise TikaPayloadTooLargeError(response=response) from cause
    # TIMEOUT and crash statuses are classified regardless of the specific non-2xx status
    # code: confirmed live that a crash envelope can appear on both 500 and 503, and there's
    # no reason to assume TIMEOUT is 503-only when it comes from the same PipesResult code path.
    if tika_status == "TIMEOUT":
        raise TikaTimeoutError(response=response) from cause
    if tika_status in {"UNSPECIFIED_CRASH", "OOM"}:
        raise TikaCrashError(response=response) from cause

    raise TikaServerError(response=response) from cause
