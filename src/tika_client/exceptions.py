# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import json
import math
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from collections.abc import Sequence

    from tika_client._http_backends._protocols import ResponseProtocol
    from tika_client.data_models import TikaResponse


class TikaError(Exception):
    """
    Root of every error this library raises.

    Exists because Tika 4 reports failures two different ways: as a non-2xx HTTP
    status (see HttpStatusError), and in-band on an HTTP 200 with the failure
    embedded in the metadata (see TikaParseError). Catching TikaError covers both.
    """


class HttpStatusError(TikaError):
    """Unified HTTP status error raised by all backends."""

    def __init__(self, *, response: ResponseProtocol) -> None:
        """Initialize the error with the response that caused it."""
        super().__init__()
        self.response = response


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


class TikaBadRequestError(TikaServerError):
    """
    A 400 response - the request is malformed, and retrying will never help.

    Covers an unknown or reserved fetcher/emitter, an unrecognized handler name in the
    path, and a malformed body. Distinct from the 5xx family because the correct
    response is to fix or drop the request rather than back off and retry.
    """


class TikaPartialParseError(TikaServerError):
    """
    A 422 response from a raw endpoint - container-level parse exception.

    Confirmed never JSON in practice: the body is either empty or the raw
    partially-extracted content, so tika_status and message end up None in real usage.
    Nothing in this class enforces that - the base class still attempts to parse the
    envelope for every response - it is an observed property of Tika's behavior rather
    than a parsing rule, so callers should not treat those attributes as guaranteed None.

    Not expected from this client. 422 comes from the raw /tika, /tika/text, /tika/html,
    /tika/xml and /tika/md family and from /meta/{field}, none of which this client calls:
    it uses /tika/json/{handler}, /meta and /rmeta, whose failures arrive as a 200 with an
    embedded exception instead. Kept for defence in depth.
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


def _is_json_content_type(headers: object) -> bool:
    """Whether the response declares a JSON body, tolerating a missing or odd header mapping."""
    getter = getattr(headers, "get", None)
    if getter is None:
        return False
    value = getter("Content-Type")
    if not isinstance(value, str):
        return False
    return "json" in value.split(";")[0].strip().lower()


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

    # These three are definitive at the protocol level, so they win over any envelope and
    # are decided before the body is touched. That also avoids running json.loads over a
    # potentially document-sized body only to discard the result.
    if status_code == 429:  # noqa: PLR2004
        raise TikaSaturatedError(response=response) from cause
    if status_code == 413:  # noqa: PLR2004
        raise TikaPayloadTooLargeError(response=response) from cause
    if status_code == 400:  # noqa: PLR2004
        raise TikaBadRequestError(response=response) from cause

    # A 422 body is the raw partially-extracted document, i.e. user-supplied content. Only
    # trust it to classify the failure when the server declares it as JSON, otherwise a
    # document that happens to extract to an envelope shape would pick its own exception.
    #
    # In practice this makes envelope classification unreachable for 422, since those bodies
    # are observed never to be JSON. That is deliberate: the gate protects against document
    # content steering control flow, and the endpoints this client calls do not return 422.
    if status_code == 422 and not _is_json_content_type(response.headers):  # noqa: PLR2004
        raise TikaPartialParseError(response=response) from cause

    tika_status, _ = _try_parse_status_envelope(response.text)

    # TIMEOUT and crash statuses are classified from the envelope rather than the status
    # code, except where the code is itself definitive (handled above): a crash envelope is
    # confirmed to appear on both 500 and 503, and TIMEOUT comes from the same PipesResult
    # code path, so neither is tied to one status code.
    if tika_status == "TIMEOUT":
        raise TikaTimeoutError(response=response) from cause
    if tika_status in {"UNSPECIFIED_CRASH", "OOM"}:
        raise TikaCrashError(response=response) from cause

    if status_code == 422:  # noqa: PLR2004
        raise TikaPartialParseError(response=response) from cause

    raise TikaServerError(response=response) from cause


class TikaParseError(TikaError):
    """
    Base for parse failures Tika 4 reports in-band on an HTTP 200.

    There is no failing HTTP response to attach, so unlike HttpStatusError these
    carry the decoded metadata that described the failure.
    """

    def __init__(self, *, data: dict[str, Any], detail: str | None) -> None:
        """Build the error from the decoded metadata of an otherwise-successful response."""
        super().__init__()
        self.data = data
        self.detail = detail

    def __str__(self) -> str:
        """Render the server-side detail, which is usually a Java stack trace."""
        return self.detail or self.__class__.__name__

    @property
    def partial(self) -> TikaResponse:
        """
        The response as parsed, so raising never discards what Tika did extract.

        Lets a caller who wants best-effort extraction recover it explicitly, which is why
        there is no flag to disable raising: try/except expresses the same choice at the call
        site, per call, rather than hiding it in client configuration.
        """
        from tika_client.data_models import TikaResponse  # noqa: PLC0415

        return TikaResponse(self.data)

    def __reduce__(self) -> tuple[Any, tuple[Any, ...]]:
        """
        Support pickle and deepcopy.

        The keyword-only __init__ leaves .args empty, so the default reduction calls
        cls(*()) and dies with a TypeError about missing arguments. These errors are
        aggregated into groups, which is exactly what crosses a process boundary under
        concurrent.futures, celery or pytest-xdist.
        """
        return (_rebuild_parse_error, (type(self), self.data, self.detail))


def _rebuild_parse_error(
    cls: type[TikaParseError],
    data: dict[str, Any],
    detail: str | None,
) -> TikaParseError:
    """Reconstruct a parse error during unpickling, since __init__ is keyword-only."""
    return cls(data=data, detail=detail)


class TikaContainerParseError(TikaParseError):
    """
    The container parser failed, so no content was extracted.

    Tika 3.x returned 500 here. Tika 4 returns 200 with the stack trace in
    tk:exception:container-exception and no tk:content, so this is raised to keep
    a failed parse from looking like an empty document.
    """


class TikaEmbeddedParseError(TikaParseError):
    """
    An embedded document failed to parse while its container succeeded.

    Only reachable from /rmeta, which returns one entry per embedded document.
    Never raised eagerly: the surrounding documents parsed fine, so this surfaces
    only via raise_for_parse_status().
    """


class TikaParseErrorGroup(ExceptionGroup[TikaParseError], TikaError):  # noqa: N818 - groups conventionally end in Group, as ExceptionGroup itself does
    """
    Every parse failure from a single /rmeta call, so none is hidden behind the first.

    An ExceptionGroup so that except* and the standard tooling work, and a TikaError so
    that it honours the same contract as every other error this library raises. A bare
    ExceptionGroup would escape "except TikaError" entirely.
    """

    # BaseExceptionGroup.derive is generic and overloaded, so any concrete narrowing is
    # reported as incompatible. Narrowing is the point: it keeps split() and subgroup()
    # returning this class rather than a plain ExceptionGroup.
    def derive(self, excs: Sequence[TikaParseError]) -> TikaParseErrorGroup:  # type: ignore[override]
        """Keep the subclass through split() and subgroup(), which would otherwise degrade to ExceptionGroup."""
        return TikaParseErrorGroup(self.message, excs)
