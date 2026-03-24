# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0
"""
Unit tests for the HTTP backend factory's auto-resolution logic.
These do not require Docker or a live Tika server.
"""

import sys

import pytest

from tika_client._http_backends import _resolve_backend


class TestResolveBackendExplicit:
    def test_httpx(self) -> None:
        assert _resolve_backend("httpx") == "httpx"

    def test_niquests(self) -> None:
        assert _resolve_backend("niquests") == "niquests"

    def test_requests(self) -> None:
        assert _resolve_backend("requests") == "requests"


class TestResolveBackendAuto:
    def test_auto_prefers_httpx(self) -> None:
        assert _resolve_backend("auto") == "httpx"

    def test_auto_falls_back_to_niquests(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setitem(sys.modules, "httpx", None)
        assert _resolve_backend("auto") == "niquests"

    def test_auto_falls_back_to_requests(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setitem(sys.modules, "httpx", None)
        monkeypatch.setitem(sys.modules, "niquests", None)
        assert _resolve_backend("auto") == "requests"

    def test_auto_raises_when_none_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setitem(sys.modules, "httpx", None)
        monkeypatch.setitem(sys.modules, "niquests", None)
        monkeypatch.setitem(sys.modules, "requests", None)
        with pytest.raises(ImportError, match="No HTTP backend available"):
            _resolve_backend("auto")
