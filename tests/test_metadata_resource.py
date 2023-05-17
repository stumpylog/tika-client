from unittest import TestCase

import magic

from tika_rest_client.client import TikaClient

from .config import SAMPLE_DIR
from .config import TIKA_URL


class TestMetadataResource(TestCase):
    def test_metadata_from_docx(self):
        with TikaClient(base_url=TIKA_URL) as client:
            test_file = SAMPLE_DIR / "sample.docx"
            client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))
            self.assertTrue(False)

    def test_metadata_from_odt(self):
        with TikaClient(base_url=TIKA_URL) as client:
            test_file = SAMPLE_DIR / "sample.odt"
            client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))
            self.assertTrue(False)
