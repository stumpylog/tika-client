from pathlib import Path

import magic

from tika_client.client import AsyncTikaClient
from tika_client.client import TikaClient


class TestParseImageMetadata:
    def test_image_jpeg(self, tika_client: TikaClient, sample_jpeg_file: Path) -> None:
        """
        Test the handling of a JPEG file metadata retrieval
        """
        resp = tika_client.metadata.from_file(sample_jpeg_file, magic.from_file(str(sample_jpeg_file), mime=True))

        assert resp.type == "image/jpeg"

    def test_image_png(self, tika_client: TikaClient, sample_png_file: Path) -> None:
        """
        Test the handling of a PNG file metadata retrieval
        """
        resp = tika_client.metadata.from_file(sample_png_file, magic.from_file(str(sample_png_file), mime=True))

        assert resp.type == "image/png"


class TestAsyncParseImageMetadata:
    async def test_image_jpeg(
        self,
        async_tika_client: AsyncTikaClient,
        sample_jpeg_file: Path,
    ) -> None:
        """
        Test the handling of a JPEG file metadata retrieval using async client
        """
        resp = await async_tika_client.metadata.from_file(
            sample_jpeg_file,
            magic.from_file(str(sample_jpeg_file), mime=True),
        )

        assert resp.type == "image/jpeg"

    async def test_image_png(
        self,
        async_tika_client: AsyncTikaClient,
        sample_png_file: Path,
    ) -> None:
        """
        Test the handling of a PNG file metadata retrieval using async client
        """
        resp = await async_tika_client.metadata.from_file(
            sample_png_file,
            magic.from_file(str(sample_png_file), mime=True),
        )

        assert resp.type == "image/png"
