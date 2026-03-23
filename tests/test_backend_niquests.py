# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0
"""
Smoke tests for the niquests HTTP backend against a real Tika server (Docker).
Tests a representative subset of routes to verify end-to-end connectivity.
"""

import logging
from collections.abc import AsyncGenerator
from collections.abc import Generator
from pathlib import Path

import pytest

from tika_client.client import AsyncTikaClient
from tika_client.client import TikaClient


@pytest.fixture
def niquests_tika_client(tika_host: str) -> Generator[TikaClient, None, None]:
    with TikaClient(tika_url=tika_host, log_level=logging.INFO, backend="niquests") as client:
        yield client


@pytest.fixture
async def async_niquests_tika_client(tika_host: str) -> AsyncGenerator[AsyncTikaClient, None]:
    async with AsyncTikaClient(tika_url=tika_host, log_level=logging.INFO, backend="niquests") as client:
        yield client


class TestNiquestsBackendSync:
    def test_metadata(self, niquests_tika_client: TikaClient, sample_docx_file: Path) -> None:
        resp = niquests_tika_client.metadata.from_file(sample_docx_file)
        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def test_tika(self, niquests_tika_client: TikaClient, sample_docx_file: Path) -> None:
        resp = niquests_tika_client.tika.as_text.from_file(sample_docx_file)
        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def test_rmeta(self, niquests_tika_client: TikaClient, sample_docx_file: Path) -> None:
        results = niquests_tika_client.rmeta.as_text.from_file(sample_docx_file)
        assert len(results) > 0
        assert results[0].type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class TestNiquestsBackendAsync:
    async def test_metadata(self, async_niquests_tika_client: AsyncTikaClient, sample_docx_file: Path) -> None:
        resp = await async_niquests_tika_client.metadata.from_file(sample_docx_file)
        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    async def test_tika(self, async_niquests_tika_client: AsyncTikaClient, sample_docx_file: Path) -> None:
        resp = await async_niquests_tika_client.tika.as_text.from_file(sample_docx_file)
        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    async def test_rmeta(self, async_niquests_tika_client: AsyncTikaClient, sample_docx_file: Path) -> None:
        results = await async_niquests_tika_client.rmeta.as_text.from_file(sample_docx_file)
        assert len(results) > 0
        assert results[0].type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
