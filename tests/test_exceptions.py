"""
Unit tests for the typed Tika server exception hierarchy.
Response bodies below are the exact bodies captured against a live apache/tika:4.0.0
server while forcing each condition (low maxRequestSizeBytes, pipes.numClients=1,
a 1ms totalTaskTimeoutMillis, and truncated/corrupted sample documents).
These do not require Docker or a live Tika server themselves.
"""

from __future__ import annotations

from typing import Any

import pytest

from tika_client.exceptions import TikaCrashError
from tika_client.exceptions import TikaPartialParseError
from tika_client.exceptions import TikaPayloadTooLargeError
from tika_client.exceptions import TikaSaturatedError
from tika_client.exceptions import TikaServerError
from tika_client.exceptions import TikaTimeoutError
from tika_client.exceptions import raise_for_tika_status


class FakeResponse:
    """A minimal stand-in satisfying ResponseProtocol for exception-parsing tests."""

    def __init__(self, status_code: int, text: str, headers: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}

    def raise_for_status(self) -> None:  # pragma: no cover - not exercised here
        pass

    def json(self) -> Any:  # noqa: ANN401 - not exercised here
        pass


class TestTimeout:
    def test_503_timeout_with_retry_after(self) -> None:
        body = (
            '{"status":"TIMEOUT","message":"java.lang.RuntimeException: '
            'Server-side progress timeout: no progress for 4ms (limit: 1ms)"}'
        )
        response = FakeResponse(503, body, headers={"Retry-After": "5"})

        with pytest.raises(TikaTimeoutError) as err:
            raise_for_tika_status(response)  # type: ignore[arg-type]

        assert err.value.tika_status == "TIMEOUT"
        assert "progress timeout" in (err.value.message or "")
        assert err.value.retry_after == 5.0
        assert err.value.status_code == 503


class TestSaturated:
    def test_429_no_message_field(self) -> None:
        response = FakeResponse(429, '{"status":"CLIENT_UNAVAILABLE_WITHIN_MS"}', headers={"Retry-After": "1"})

        with pytest.raises(TikaSaturatedError) as err:
            raise_for_tika_status(response)  # type: ignore[arg-type]

        assert err.value.tika_status == "CLIENT_UNAVAILABLE_WITHIN_MS"
        assert err.value.message is None
        assert err.value.retry_after == 1.0

    def test_429_non_string_retry_after_header_does_not_escape_as_type_error(self) -> None:
        # A multi-value header mapping may hand back a list rather than a str; float()
        # would raise TypeError, which must not escape exception construction.
        response = FakeResponse(429, '{"status":"CLIENT_UNAVAILABLE_WITHIN_MS"}', headers={"Retry-After": ["5"]})

        with pytest.raises(TikaSaturatedError) as err:
            raise_for_tika_status(response)  # type: ignore[arg-type]

        assert err.value.tika_status == "CLIENT_UNAVAILABLE_WITHIN_MS"
        assert err.value.retry_after is None
        assert err.value.status_code == 429


class TestPayloadTooLarge:
    def test_413_plain_text_body(self) -> None:
        response = FakeResponse(413, "Request body exceeds maxRequestSizeBytes")

        with pytest.raises(TikaPayloadTooLargeError) as err:
            raise_for_tika_status(response)  # type: ignore[arg-type]

        assert err.value.tika_status is None
        assert err.value.response_text == "Request body exceeds maxRequestSizeBytes"

    def test_413_json_body(self) -> None:
        response = FakeResponse(413, '{"status":"PAYLOAD_LIMIT_EXCEEDED"}')

        with pytest.raises(TikaPayloadTooLargeError) as err:
            raise_for_tika_status(response)  # type: ignore[arg-type]

        assert err.value.tika_status == "PAYLOAD_LIMIT_EXCEEDED"


class TestPartialParse:
    def test_422_empty_body(self) -> None:
        response = FakeResponse(422, "")

        with pytest.raises(TikaPartialParseError) as err:
            raise_for_tika_status(response)  # type: ignore[arg-type]

        assert err.value.response_text == ""
        assert err.value.tika_status is None

    def test_422_partial_content_body_is_not_parsed_as_json(self) -> None:
        response = FakeResponse(422, "<html><body>partial content, not JSON</body>")

        with pytest.raises(TikaPartialParseError) as err:
            raise_for_tika_status(response)  # type: ignore[arg-type]

        assert err.value.response_text == "<html><body>partial content, not JSON</body>"
        assert err.value.tika_status is None


class TestCrashInference:
    def test_503_oom_status_maps_to_crash_error(self) -> None:
        response = FakeResponse(503, '{"status":"OOM"}')

        with pytest.raises(TikaCrashError) as err:
            raise_for_tika_status(response)  # type: ignore[arg-type]

        assert err.value.tika_status == "OOM"

    def test_500_oom_status_also_maps_to_crash_error(self) -> None:
        """A 500 (not just 503) carrying an OOM status envelope is still a crash, not a bare TikaServerError."""
        response = FakeResponse(500, '{"status":"OOM"}')

        with pytest.raises(TikaCrashError) as err:
            raise_for_tika_status(response)  # type: ignore[arg-type]

        assert err.value.tika_status == "OOM"
        assert err.value.status_code == 500


class TestFallback:
    def test_unrecognized_status_code_falls_back_to_base_error(self) -> None:
        response = FakeResponse(418, "I'm a teapot")

        with pytest.raises(TikaServerError) as err:
            raise_for_tika_status(response)  # type: ignore[arg-type]

        assert not isinstance(err.value, (TikaTimeoutError, TikaCrashError, TikaSaturatedError))
        assert err.value.response_text == "I'm a teapot"

    def test_500_with_json_envelope_is_not_json_gated_to_specific_codes(self) -> None:
        response = FakeResponse(500, '{"status":"FAILED_TO_INITIALIZE","message":"config error"}')

        with pytest.raises(TikaServerError) as err:
            raise_for_tika_status(response)  # type: ignore[arg-type]

        assert err.value.tika_status == "FAILED_TO_INITIALIZE"
        assert err.value.message == "config error"

    def test_2xx_does_not_raise(self) -> None:
        response = FakeResponse(200, '{"ok": true}')
        raise_for_tika_status(response)  # type: ignore[arg-type]  # must not raise
