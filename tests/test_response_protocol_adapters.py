# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0

"""
Unit tests for the text/headers surface added to ResponseProtocol.
These construct response objects directly and do not require Docker or a live Tika server.
"""

import httpx
import requests

from tika_client._http_backends._httpx import HttpxResponseAdapter
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
