# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0
"""
Smoke tests for the requests HTTP backend against a real Tika server (Docker).
Tests a representative subset of routes to verify end-to-end connectivity.
Note: requests is sync-only; async usage raises ValueError.
"""

import logging
from collections.abc import Generator
from pathlib import Path

import pytest

from tika_client.client import AsyncTikaClient
from tika_client.client import TikaClient


@pytest.fixture
def requests_tika_client(tika_host: str) -> Generator[TikaClient, None, None]:
    with TikaClient(tika_url=tika_host, log_level=logging.INFO, backend="requests") as client:
        yield client


class TestRequestsBackendSync:
    def test_metadata(self, requests_tika_client: TikaClient, sample_docx_file: Path) -> None:
        resp = requests_tika_client.metadata.from_file(sample_docx_file)
        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def test_tika(self, requests_tika_client: TikaClient, sample_docx_file: Path) -> None:
        resp = requests_tika_client.tika.as_text.from_file(sample_docx_file)
        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def test_rmeta(self, requests_tika_client: TikaClient, sample_docx_file: Path) -> None:
        results = requests_tika_client.rmeta.as_text.from_file(sample_docx_file)
        assert len(results) > 0
        assert results[0].type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class TestRequestsBackendAsyncRejected:
    async def test_async_raises(self, tika_host: str) -> None:
        with pytest.raises(ValueError, match=r"requests.*does not support async"):
            _ = AsyncTikaClient(tika_url=tika_host, backend="requests").client
