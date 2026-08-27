# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0
"""
Tests that from_file() streams rather than buffering the whole file.

Tika 4 removed the /tika/form routes, so these calls became a raw PUT. The first
implementation read the file with read_bytes(), making memory use scale with file size,
which matters more now that maxRequestSizeBytes defaults to 1 GiB.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tika_client.client import AsyncTikaClient
from tika_client.client import TikaClient
from tika_client.exceptions import TikaContainerParseError


@pytest.fixture
def no_whole_file_reads(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make any attempt to slurp a file fail, so buffering cannot pass silently."""

    def refuse(self: Path) -> bytes:
        msg = f"from_file must stream {self.name}, not read it into memory"
        raise AssertionError(msg)

    monkeypatch.setattr(Path, "read_bytes", refuse)


@pytest.mark.usefixtures("no_whole_file_reads")
class TestSyncFromFileStreams:
    def test_as_text_streams(self, tika_client: TikaClient, sample_docx_file: Path) -> None:
        """Plain text extraction sends the file without reading it whole."""
        result = tika_client.tika.as_text.from_file(sample_docx_file)

        assert result.content is not None

    def test_as_html_streams(self, tika_client: TikaClient, sample_docx_file: Path) -> None:
        """HTML extraction sends the file without reading it whole."""
        result = tika_client.tika.as_html.from_file(sample_docx_file)

        assert result.content is not None


@pytest.mark.usefixtures("no_whole_file_reads")
class TestAsyncFromFileStreams:
    async def test_as_text_streams(self, async_tika_client: AsyncTikaClient, sample_docx_file: Path) -> None:
        """The async path streams too, rather than reading in a worker thread."""
        result = await async_tika_client.tika.as_text.from_file(sample_docx_file)

        assert result.content is not None

    async def test_as_html_streams(self, async_tika_client: AsyncTikaClient, sample_docx_file: Path) -> None:
        """The async HTML path streams as well."""
        result = await async_tika_client.tika.as_html.from_file(sample_docx_file)

        assert result.content is not None


class TestZeroByteFiles:
    """
    An empty file must not be streamed.

    requests and niquests compute the body length from the handle, and a zero length is
    falsy, so they add Transfer-Encoding: chunked without dropping our Content-Length: 0.
    Jetty, which tika-server runs on, rejects that pairing with a 400. These run across
    every backend because the default-only fixtures are how the regression got in.
    """

    @pytest.mark.parametrize("backend", ["httpx", "niquests", "requests"])
    def test_empty_file_reaches_tika(self, tika_host: str, backend: str, tmp_path: Path) -> None:
        """Tika must see the upload and report it as empty, rather than Jetty rejecting the framing."""
        empty = tmp_path / "empty.txt"
        empty.write_bytes(b"")

        # Tika reports a zero-byte input as a container failure, which is the correct answer.
        # A 400 would mean the request never got that far.
        with (
            TikaClient(tika_url=tika_host, backend=backend) as client,
            pytest.raises(TikaContainerParseError) as err,
        ):
            client.tika.as_text.from_file(empty)

        assert "ZeroByteFileException" in str(err.value)

    @pytest.mark.parametrize("backend", ["httpx", "niquests"])
    async def test_empty_file_reaches_tika_async(self, tika_host: str, backend: str, tmp_path: Path) -> None:
        """The async paths share put_file, so they share the empty-body handling."""
        empty = tmp_path / "empty.txt"
        empty.write_bytes(b"")

        async with AsyncTikaClient(tika_url=tika_host, backend=backend) as client:
            with pytest.raises(TikaContainerParseError) as err:
                await client.tika.as_text.from_file(empty)

        assert "ZeroByteFileException" in str(err.value)
