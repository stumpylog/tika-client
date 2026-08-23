# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0

"""
Unit tests for the text/headers surface added to ResponseProtocol.
These construct response objects directly and do not require Docker or a live Tika server.
"""

import httpx
import niquests
import requests

from tika_client._http_backends._httpx import HttpxResponseAdapter
from tika_client._http_backends._niquests import NiquestsResponseAdapter
from tika_client._http_backends._requests import RequestsResponseAdapter


class TestHttpxResponseAdapterTextHeaders:
    def test_text_and_headers(self) -> None:
        raw = httpx.Response(413, text="Request body exceeds maxRequestSizeBytes", headers={"Retry-After": "5"})
        adapter = HttpxResponseAdapter(raw)

        assert adapter.text == "Request body exceeds maxRequestSizeBytes"
        assert adapter.headers["Retry-After"] == "5"


class TestRequestsResponseAdapterTextHeaders:
    def test_text_and_headers(self) -> None:
        raw = requests.Response()
        raw.status_code = 413
        raw._content = b"Request body exceeds maxRequestSizeBytes"  # noqa: SLF001
        raw.headers["Retry-After"] = "5"
        adapter = RequestsResponseAdapter(raw)

        assert adapter.text == "Request body exceeds maxRequestSizeBytes"
        assert adapter.headers["Retry-After"] == "5"


class TestNiquestsResponseAdapterTextHeaders:
    def test_text_and_headers(self) -> None:
        raw = niquests.Response()
        raw.status_code = 413
        raw._content = b"Request body exceeds maxRequestSizeBytes"  # noqa: SLF001
        raw.headers["Retry-After"] = "5"
        adapter = NiquestsResponseAdapter(raw)

        assert adapter.text == "Request body exceeds maxRequestSizeBytes"
        assert adapter.headers["Retry-After"] == "5"

    def test_text_none_falls_back_to_empty_string(self) -> None:
        """
        niquests' Response.text returns None (rather than "") when the response's encoding
        resolves to a non-text codec (e.g. "base64_codec"). The adapter's `.text` property
        must never surface None, since callers (e.g. `raise_for_tika_status`) treat it as `str`.
        """
        raw = niquests.Response()
        raw._content = b"hello"  # noqa: SLF001
        raw.encoding = "base64_codec"
        assert raw.text is None  # sanity-check the underlying behavior we're guarding against

        adapter = NiquestsResponseAdapter(raw)

        assert adapter.text == ""
