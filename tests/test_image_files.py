import magic

from tests.conftest import SAMPLE_DIR
from tika_client.client import TikaClient


class TestParseImageMetadata:
    def test_image_jpeg(self, tika_client: TikaClient):
        """
        Test the handling of a JPEG file metadata retrieval
        """
        test_file = SAMPLE_DIR / "sample.jpg"
        resp = tika_client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert resp.type == "image/jpeg"

    def test_image_png(self, tika_client: TikaClient):
        """
        Test the handling of a PNG file metadata retrieval
        """
        test_file = SAMPLE_DIR / "sample.png"
        resp = tika_client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert resp.type == "image/png"
